import argparse
import os
import sys
import yaml
import json
from wisup_e2m import E2MParser, TextConverter
import logging
from datetime import datetime
from pathlib import Path
import litellm
import regex as re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_anthropic_key(api_key):
    """Test if the Anthropic API key is valid by making a minimal test request"""
    try:
        # Create minimal test message to validate auth
        messages = [{"role": "user", "content": "test"}]
        completion = litellm.completion(
            model="claude-3-haiku-20240307",
            messages=messages,
            api_key=api_key,
            max_tokens=1  # Minimize token usage for validation
        )
        return True
    except litellm.exceptions.AuthenticationError as e:
        logger.error(f"Authentication failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False

def resolve_api_key(config_api_key):
    """Resolve API key from config or environment with proper variable substitution"""
    if not config_api_key:
        return os.getenv('ANTHROPIC_API_KEY')
    
    if config_api_key.startswith('${') and config_api_key.endswith('}'):
        env_var = config_api_key[2:-1]  # Remove ${ and }
        return os.getenv(env_var)
    
    return config_api_key

def setup_argparser():
    parser = argparse.ArgumentParser(description='Convert PDF files to Markdown using e2m')
    parser.add_argument('pdf_files', nargs='+', help='One or more PDF files to convert')
    parser.add_argument('--output-dir', '-o', default='output',
                       help='Output directory for markdown files (default: output)')
    parser.add_argument('--intermediate-dir', '-t', default='intermediate',
                       help='Directory for intermediate parsed content (default: intermediate)')
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--image-dir', '-i', default='figures',
                       help='Directory for extracted images (default: figures)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    return parser

class ContentPreservingConverter:
    """Enhanced converter that better handles academic paper formatting and book structures"""
    
    def __init__(self, text_converter, intermediate_dir, chunk_size=2000, overlap=300):
        self.text_converter = text_converter
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.intermediate_dir = intermediate_dir
        self.system_prompt = """You are performing conversion of PDF content to clean, well-structured Markdown. Your task is to:

1. Identify and preserve the document's logical structure while removing non-content elements:
   - Remove headers, footers, page numbers, and journal information
   - Remove repeated metadata like DOIs, ISBNs, and copyright notices
   - Remove author contact information unless it's part of the main content
   - Keep and properly format author names and affiliations in the header section
   
2. Apply appropriate Markdown formatting:
   - Use # for main title
   - Use ## for section headings
   - Use ### for subsection headings
   - Format lists with proper Markdown bullet points or numbers
   - Preserve emphasis (bold/italic) where it appears in the original
   - Format citations and references properly
   - Convert figure references to Markdown image syntax
   - Use appropriate blockquotes (>) for quoted content
   - Use proper line breaks and spacing between sections
   
3. Clean up typical PDF conversion artifacts:
   - Remove unnecessary line breaks within paragraphs
   - Fix hyphenation at line breaks
   - Remove repeated whitespace
   - Fix common OCR errors in special characters
   - Properly handle multi-column layouts
   - Remove or fix artifacts from equations and special characters

4. Special handling for academic papers:
   - Preserve the abstract as a separate section
   - Maintain proper formatting of equations
   - Keep figure and table captions
   - Preserve citation numbers and reference formatting
   - Handle footnotes appropriately

5. Preserve structured information:
   - Maintain the logical flow of the document
   - Keep all content in its proper context
   - Preserve hierarchical relationships between sections
   - Maintain proper ordering of content

Do not:
- Add or remove any actual content
- Rephrase or paraphrase text
- Reorganize the document structure
- Combine or split sections unless fixing obvious layout issues
- Add explanatory text or comments

The goal is a clean, properly formatted Markdown document that maintains the exact content and structure of the original PDF while removing artifacts and applying correct Markdown syntax."""

    def _preprocess_text(self, text):
        """Preprocess text to handle common PDF conversion issues"""
        # Remove repeated headers/footers often found in PDFs
        text = re.sub(r'(?m)^[\d\s]*$', '', text)  # Remove standalone page numbers
        
        # Remove common academic paper headers/footers
        patterns_to_remove = [
            r'(?m)^.*?(?:Informatik Spektrum|DOI:|ISSN:).*$\n?',
            r'(?m)^.*?(?:Received:|Accepted:|Published).*?202\d.*$\n?',
            r'(?m)^.*?©.*?202\d.*$\n?',
            r'(?m)^.*?Creative Commons.*$\n?',
            r'(?m)^.*?http.*$\n?',  # Remove URLs in headers/footers
            r'@ Springer\s*$\n?'
        ]
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Fix hyphenation while preserving paragraph breaks
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Clean up whitespace more carefully
        text = re.sub(r' +', ' ', text)  # Collapse multiple spaces
        text = re.sub(r'\t+', ' ', text)  # Convert tabs to spaces
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Collapse multiple blank lines to two
        text = re.sub(r'(?<=\S) +(?=\n)', '', text)  # Remove trailing spaces
        text = re.sub(r'^ +', '', text, flags=re.MULTILINE)  # Remove leading spaces
        
        # Fix special characters
        text = text.replace('¨', '')  # Remove diaeresis artifacts
        text = text.replace('´', "'")  # Replace weird quotes
        text = text.replace('’', "'")  # Normalize quotes
        text = text.replace('“', '"').replace('”', '"')  # Normalize quotes
        
        return text.strip()

    def _identify_document_structure(self, text):
        """Identify the main structural elements of the document"""
        structure = {
            'title': None,
            'authors': None,
            'abstract': None,
            'sections': []
        }
        
        # Find title (usually first significant line)
        lines = text.split('\n')
        for line in lines[:10]:  # Look in first 10 lines
            if len(line.strip()) > 20 and not line.startswith('http'):
                structure['title'] = line.strip()
                break
        
        # Identify abstract
        abstract_match = re.search(r'(?i)abstract.*?\n(.*?)(?=\n\s*[A-Z][^a-z]*$)', text, re.DOTALL)
        if abstract_match:
            structure['abstract'] = abstract_match.group(1).strip()
        
        # Find main sections
        section_pattern = r'^[A-Z][^a-z\n]{0,100}$'  # Uppercase lines are likely sections
        structure['sections'] = re.findall(section_pattern, text, re.MULTILINE)
        
        return structure

    def _format_to_markdown(self, text, structure):
        """Convert text to properly formatted Markdown based on identified structure"""
        md_lines = []
        
        # Add title
        if structure['title']:
            md_lines.append(f"# {structure['title'].strip()}\n")
        
        # Add abstract if present
        if structure['abstract']:
            md_lines.append("## Abstract\n")
            md_lines.append(f"{structure['abstract'].strip()}\n")
        
        # Process main content
        current_text = text
        
        # Convert section headers (but not if they're already markdown)
        for section in structure['sections']:
            section = section.strip()
            if section and not section.startswith('#'):
                # Replace full line to preserve surrounding whitespace
                current_text = re.sub(
                    f"^{re.escape(section)}$",
                    f"## {section}",
                    current_text,
                    flags=re.MULTILINE
                )
        
        # Format lists while preserving indentation
        current_text = re.sub(r'(?m)^(\s*)[\-•]\s*', r'\1* ', current_text)
        current_text = re.sub(r'(?m)^(\s*\d+\.)\s*', r'\1 ', current_text)
        
        # Format figure references
        current_text = re.sub(
            r'(?i)(?:abb\.|abbildung|fig\.|figure)\s*(\d+)',
            r'![Figure \1](figures/figure-\1.jpg)',
            current_text
        )
        
        # Format quotes
        current_text = re.sub(
            r'(?m)^(\s*)["""](.*?)["""]$',
            r'\1> \2',
            current_text
        )
        
        # Ensure proper line breaks between sections
        current_text = re.sub(r'\n{3,}', '\n\n', current_text)
        
        # Add processed content
        md_lines.append(current_text)
        
        # Join with proper line breaks and clean up any remaining artifacts
        result = "\n".join(md_lines)
        
        # Post-processing cleanup
        result = re.sub(r'\n{3,}', '\n\n', result)  # No more than 2 consecutive line breaks
        result = re.sub(r'(^|\n)[\s\-_]+($|\n)', r'\1\2', result)  # Remove separator lines
        result = re.sub(r'  +', ' ', result)  # Remove multiple spaces
        
        return result
    
    
    def _split_into_chunks(self, text):
        """Split text into chunks, preserving paragraph boundaries and headers"""
        # Split on clear section boundaries if possible
        sections = re.split(r'(?=^#+\s|^[A-Z][^a-z\n]*$)', text, flags=re.MULTILINE)
        
        if len(sections) == 1:  # If no clear sections, split on paragraphs
            sections = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for section in sections:
            section_size = len(section)
            if current_size + section_size > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                # Keep last section for overlap if it's not a header
                if not re.match(r'^#+\s|^[A-Z][^a-z\n]*$', current_chunk[-1]):
                    current_chunk = [current_chunk[-1]]
                    current_size = len(current_chunk[-1])
                else:
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(section)
            current_size += section_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def convert(self, text):
        """Convert text while preserving content and applying proper Markdown formatting"""
        # Initial preprocessing
        text = self._preprocess_text(text)
        
        # Identify document structure
        structure = self._identify_document_structure(text)
        
        # Split into manageable chunks
        chunks = self._split_into_chunks(text)
        logger.info(f"Split document into {len(chunks)} chunks")
        
        # Process each chunk
        converted_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                converted = self._convert_chunk(chunk)
                converted_chunks.append(converted)
            except Exception as e:
                logger.error(f"Error converting chunk {i+1}: {str(e)}")
                converted_chunks.append(chunk)
        
        # Combine chunks and apply final formatting
        combined = self._combine_chunks(converted_chunks)
        final_markdown = self._format_to_markdown(combined, structure)
        
        # Remove any duplicate content that might have been introduced
        final_markdown = self._remove_duplicates(final_markdown)
        
        return final_markdown
    
    def _convert_chunk(self, chunk):
            """Convert a single chunk with document-type awareness"""
            try:
                # Add system prompt and clear instructions for this chunk
                prompt = f"{self.system_prompt}\n\nCONVERT THIS TEXT TO MARKDOWN:\n\n{chunk}"
                
                converted = self.text_converter.convert(prompt)
                
                # Clean up any prompt reflections
                converted = re.sub(r'^You are performing.*?MARKDOWN:', '', converted, flags=re.DOTALL)
                converted = converted.strip()
                
                # Basic validation
                if len(converted) < len(chunk) * 0.8:
                    logger.warning(f"Chunk shows potential content loss - saving for analysis")
                    os.makedirs(self.intermediate_dir, exist_ok=True)
                    
                    with open(os.path.join(self.intermediate_dir, "chunk_original.txt"), 'w', encoding='utf-8') as f:
                        f.write(chunk)
                    with open(os.path.join(self.intermediate_dir, "chunk_converted.md"), 'w', encoding='utf-8') as f:
                        f.write(converted)
                    
                    # Use original if conversion lost too much
                    return chunk
                
                # Clean up common markdown formatting issues
                converted = self._clean_markdown_formatting(converted)
                
                return converted
                
            except Exception as e:
                logger.error(f"Error in chunk conversion: {str(e)}")
                return chunk
            
    def _clean_markdown_formatting(self, text):
        """Clean up common markdown formatting issues"""
        # Fix headers that might have extra hash marks
        text = re.sub(r'(#{1,6})\s*#{1,6}\s', r'\1 ', text)
        
        # Ensure proper spacing around headers
        text = re.sub(r'(\n#{1,6}[^\n]+)(\n[^#\n])', r'\1\n\2', text)
        
        # Fix list item spacing
        text = re.sub(r'(\n[*-]\s[^\n]+)(\n[^*\n-])', r'\1\n\2', text)
        
        # Properly format blockquotes
        text = re.sub(r'(\n>\s[^\n]+)(\n[^>\n])', r'\1\n\2', text)
        
        # Fix extra whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'^ +', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _find_overlap(self, text1, text2):
        """Find the largest overlapping text between two chunks"""
        # Look for overlap starting with larger sequences
        min_overlap = 50  # Minimum meaningful overlap
        max_overlap = min(len(text1), len(text2), self.overlap)
        
        # Try decreasing sizes of overlap
        for size in range(max_overlap, min_overlap, -1):
            end_of_first = text1[-size:].strip()
            if len(end_of_first) == 0:
                continue
                
            # Look for this sequence at start of second text
            try:
                position = text2.index(end_of_first)
                # If we found it and it's near the start, that's our overlap
                if position < 100:  # Only consider matches near start of second chunk
                    return position + len(end_of_first)
            except ValueError:
                continue
        
        # No significant overlap found
        return 0

    def _combine_chunks(self, chunks):
        """Combine chunks while handling overlap and preventing header duplication"""
        if not chunks:
            return ""
            
        result = chunks[0]
        
        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            # Find any overlapping content
            overlap_start = self._find_overlap(result, next_chunk)
            
            if overlap_start > 0:
                # Avoid duplicate headers in overlap
                next_content = next_chunk[overlap_start:]
                if next_content.strip().startswith('#'):
                    # Check if header already exists in result
                    header_end = next_content.find('\n')
                    if header_end == -1:
                        header_end = len(next_content)
                    header = next_content[:header_end]
                    if header in result[-200:]:  # Check last 200 chars for duplicate header
                        next_content = next_content[header_end:].strip()
                result += '\n\n' + next_content
            else:
                # If no overlap found, ensure proper spacing between chunks
                result += '\n\n' + next_chunk
        
        return result.strip()

    def _remove_duplicates(self, text):
        """Remove any duplicate paragraphs or sections while preserving order"""
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        
        for line in lines:
            # Skip empty lines or very short lines
            if len(line.strip()) < 10:
                unique_lines.append(line)
                continue
                
            # Create a normalized version for comparison
            normalized = re.sub(r'\s+', ' ', line.strip().lower())
            
            if normalized not in seen:
                seen.add(normalized)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
class PDF2Markdown:
    def __init__(self, pdf_files, output_dir, intermediate_dir, config, image_dir, debug):
        self.pdf_files = pdf_files
        self.output_dir = output_dir if output_dir else 'output'
        self.intermediate_dir = intermediate_dir if intermediate_dir else 'intermediate'
        self.config = config if config else Path(__file__).parent / 'config.yaml'
        self.image_dir = image_dir if image_dir else 'figures'
        self.debug = debug if debug else False
        
        # Load config first
        with open(self.config, 'r') as f:
            self.config_data = yaml.safe_load(f)

        # Get converter config
        converter_config = self.config_data.get('converters', {}).get('text_converter', {})

        
        # Resolve API key
        self.api_key = resolve_api_key(converter_config.get('api_key'))
        if not self.api_key:
            raise ValueError("No API key found. Set ANTHROPIC_API_KEY environment variable or configure in config.yaml")

        # Initialize text converter
        self.text_converter = TextConverter(
            engine=converter_config.get('engine'),
            model=converter_config.get('model'),
            api_key=self.api_key,
            base_url=converter_config.get('base_url', ''),
            caching=False
        )
        # Initialize content-preserving converter
        self.content_converter = ContentPreservingConverter(
            self.text_converter,
            self.intermediate_dir,
            chunk_size=4000,  # Adjust based on model token limits
            overlap=200
        )
        


        # Validate API key before proceeding
        if not validate_anthropic_key(self.api_key):
            raise ValueError("Invalid Anthropic API key. Please check your configuration.")
        
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.intermediate_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

        # Initialize parser
        self.parser = E2MParser.from_config(self.config)

    def _merge_hyphenated_words(self, text):
        """Fix hyphenation issues across line breaks"""
        # Pattern matches hyphenated words across line breaks
        pattern = r'(\w+)-\s*\n\s*(\w+)'
        # Replace with merged words
        return re.sub(pattern, r'\1\2', text)


    def parse_pdf_files(self):
        for pdf_file in self.pdf_files:
            logger.info(f'Processing file: {pdf_file}')
            try:
                # Parse PDF
                parsed_data = self.parser.parse(
                    pdf_file,
                    work_dir=os.getcwd(),
                    image_dir=self.image_dir
                )
                
                # Fix hyphenation in original text
                fixed_text = self._merge_hyphenated_words(parsed_data.text)
                parsed_data.text = fixed_text
                os.makedirs(self.intermediate_dir, exist_ok=True)
                with open(Path(self.intermediate_dir) / f"{Path(pdf_file).stem}.json", 'w', encoding='utf-8') as f:
                    json.dump(parsed_data.metadata, f, indent=4)
                with open(Path(self.intermediate_dir) / f"{Path(pdf_file).stem}.txt", 'w', encoding='utf-8') as f:
                    f.write(parsed_data.text)
                # Save original content length for verification
                
                
                original_length = len(parsed_data.text)
                logger.info(f"Original content length: {original_length} characters")
                
                # Convert text content using content-preserving converter
                if parsed_data.text:
                    markdown_content = self.content_converter.convert(parsed_data.text)
                    
                    # Verify content preservation
                    converted_length = len(markdown_content)
                    logger.info(f"Converted content length: {converted_length} characters")
                    
                    # More strict content preservation check
                    if converted_length < original_length * 0.9:  # Now requiring 90% preservation
                        logger.error("Significant content loss detected!")
                        if self.debug:
                            # Save both versions for comparison
                            debug_dir = Path(self.intermediate_dir) / f"debug_{Path(pdf_file).stem}"
                            os.makedirs(debug_dir, exist_ok=True)
                            
                            with open(debug_dir / "original.txt", 'w', encoding='utf-8') as f:
                                f.write(fixed_text)
                            with open(debug_dir / "converted.md", 'w', encoding='utf-8') as f:
                                f.write(markdown_content)
                            
                            # Also save character count comparison
                            with open(debug_dir / "comparison.txt", 'w', encoding='utf-8') as f:
                                f.write(f"Original length: {original_length}\n")
                                f.write(f"Converted length: {converted_length}\n")
                                f.write(f"Preservation ratio: {converted_length/original_length:.2%}\n")
                    
                    # Save the markdown content
                    pdf_name = Path(pdf_file).stem
                    output_file = Path(self.output_dir) / f"{pdf_name}.md"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    
                    logger.info(f'Successfully converted {pdf_file} to {output_file}')
                
                # Save intermediate content if in debug mode
                if self.debug:
                    intermediate_dir = Path(self.intermediate_dir) / f"{pdf_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.makedirs(intermediate_dir, exist_ok=True)
                    
                    with open(intermediate_dir / "raw_text.txt", 'w', encoding='utf-8') as f:
                        f.write(parsed_data.text)
                    
                    with open(intermediate_dir / "metadata.json", 'w', encoding='utf-8') as f:
                        json.dump(parsed_data.metadata, f, indent=4)
                
            except Exception as e:
                logger.error(f'Error processing {pdf_file}: {str(e)}')
                if self.debug:
                    raise

def main():
    parser = setup_argparser()
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        
    try:
        pdf2md = PDF2Markdown(
            args.pdf_files,
            args.output_dir,
            args.intermediate_dir,
            args.config,
            args.image_dir,
            args.debug
        )
        pdf2md.parse_pdf_files()
        logger.info('Conversion completed successfully!')
        
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f'Fatal error: {str(e)}')
        if args.debug:
            raise
        sys.exit(1)

if __name__ == '__main__':
    main()