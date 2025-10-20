"""
Data Processing Script - Converts raw data to clean markdown
Uses Claude API to create parent-friendly content
Windows-compatible (no emoji characters)
"""

import os
import json
from pathlib import Path
import PyPDF2
from bs4 import BeautifulSoup
import anthropic
from dotenv import load_dotenv
import time

load_dotenv()


class EnhancedDataProcessor:
    """Processes raw data into knowledge base markdown files"""
    
    def __init__(self):
        self.raw_dir = Path("data/raw")
        self.kb_dir = Path("knowledge-base")
        self.structured_dir = Path("data/structured")
        
        # Initialize Claude
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        
        self.claude = anthropic.Anthropic(api_key=api_key)
        
        print("[OK] Claude API initialized")
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"  [ERROR] Error reading PDF: {e}")
            return ""
    
    def extract_html_text(self, html_path: Path) -> str:
        """Extract text from HTML"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            return text
        except Exception as e:
            print(f"  [ERROR] Error reading HTML: {e}")
            return ""
    
    def ask_claude(self, prompt: str, max_tokens: int = 2000) -> str:
        """Ask Claude to process content"""
        try:
            message = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text
        except Exception as e:
            print(f"  [ERROR] Claude API error: {e}")
            return ""
    
    # ==================== PREGNANCY CONTENT ====================
    
    def process_pregnancy_week(self, html_path: Path, week: int):
        """Convert pregnancy week HTML to parent-friendly markdown"""
        print(f"  Processing week {week}...")
        
        html_text = self.extract_html_text(html_path)
        
        if not html_text:
            print(f"  [ERROR] Could not extract text from {html_path}")
            return
        
        prompt = f"""Using this pregnancy information for week {week} as reference, create a warm, helpful guide for expecting parents.

SOURCE TEXT (excerpt):
{html_text[:3000]}

Create a guide with these sections:
1. **Your Baby This Week** (2-3 sentences about baby's development)
2. **Your Body This Week** (2-3 sentences about mom's changes)
3. **This Week's To-Do** (1-3 actionable items)
4. **Tips for Partners** (1-2 ways partner can help)

Tone: Warm, encouraging, informative
Format: Markdown with clear headers
Length: 300-400 words
End with: "Source: Pregnancy guides (Educational use)"

Important: Paraphrase in your own words, do not quote directly."""
        
        markdown = self.ask_claude(prompt)
        
        if markdown:
            output_path = self.kb_dir / "pregnancy" / f"week_{week}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"  [OK] Saved to {output_path.name}")
            time.sleep(2)
        else:
            print(f"  [ERROR] Failed to generate content")
    
    def process_pregnancy_vaccines(self):
        """Process pregnancy vaccine information"""
        print("\n[PREGNANCY VACCINES] Processing pregnancy vaccine guides...")
        
        vaccine_topics = [
            ("tdap", "Tdap vaccine during pregnancy"),
            ("flu", "Flu vaccine during pregnancy")
        ]
        
        for vaccine_code, vaccine_name in vaccine_topics:
            html_path = self.raw_dir / f"pregnancy_vaccine_{vaccine_code}.html"
            
            if not html_path.exists():
                print(f"  [SKIP] {vaccine_name} file not found")
                continue
            
            print(f"  Processing {vaccine_name}...")
            
            html_text = self.extract_html_text(html_path)
            
            if not html_text:
                continue
            
            prompt = f"""Using this CDC information about {vaccine_name}, create a guide for pregnant women.

SOURCE TEXT (excerpt):
{html_text[:3000]}

Create a guide with:
1. **Why This Vaccine During Pregnancy** (2-3 sentences)
2. **When to Get It** (specific timing)
3. **How It Protects Baby** (explain antibody transfer)
4. **Is It Safe?** (address common concerns)
5. **Side Effects** (what's normal)

Tone: Reassuring, evidence-based, clear
Format: Markdown
Length: 300-400 words
End with: "Source: CDC Pregnancy Vaccine Guidelines (Public Domain)"

Paraphrase in your own words."""
            
            markdown = self.ask_claude(prompt)
            
            if markdown:
                output_path = self.kb_dir / "pregnancy" / f"{vaccine_code}_vaccine.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
                print(f"  [OK] Saved to {output_path.name}")
                time.sleep(2)
    
    def create_pregnancy_shopping_guide(self):
        """Create what-to-buy guide from JSON data"""
        print("\n[SHOPPING] Creating pregnancy shopping guide...")
        
        # Load purchase timeline
        purchase_file = self.structured_dir / "purchase_timeline.json"
        with open(purchase_file, 'r') as f:
            purchases = json.load(f)
        
        prompt = f"""Using this purchase timeline data, create a comprehensive shopping guide for expecting parents.

DATA:
{json.dumps(purchases, indent=2)}

Create a guide with:
1. **Big Purchases (Buy Early - Weeks 20-28)**
   - List each item with why timing matters
   - Include budget ranges
   - Safety considerations
   
2. **Hospital Bag Essentials (Pack by Week 32)**
   - Categorized by: For Baby, For Mom
   
3. **Can Wait Until After Birth**
   - Items you don't need immediately
   
4. **Money-Saving Tips**
   - 3-4 practical tips

Tone: Practical, budget-conscious, reassuring
Format: Markdown with clear sections
Length: 500-600 words

Write in your own words, making it helpful and organized."""
        
        markdown = self.ask_claude(prompt, max_tokens=3000)
        
        if markdown:
            output_path = self.kb_dir / "pregnancy" / "shopping_guide.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"  [OK] Saved shopping guide")
            time.sleep(2)
    
    # ==================== BABY VACCINES ====================
    
    def process_vaccine_pdf(self, pdf_path: Path, vaccine_name: str):
        """Convert vaccine PDF to parent-friendly markdown"""
        print(f"  Processing {vaccine_name} vaccine...")
        
        pdf_text = self.extract_pdf_text(pdf_path)
        
        if not pdf_text:
            print(f"  [ERROR] Could not extract text from {pdf_path}")
            return
        
        prompt = f"""Using this CDC Vaccine Information Statement as reference, create a warm, parent-friendly guide about the {vaccine_name} vaccine.

SOURCE TEXT (excerpt):
{pdf_text[:3000]}

Create a guide with these sections:
1. **What It Protects Against** (2-3 sentences, simple language)
2. **When It's Given** (specific ages)
3. **What to Expect**
   - How it's given (shot vs oral)
   - Common side effects that are NORMAL
4. **How to Care for Your Baby After**
   - Comfort measures
   - When fever reducers are OK
5. **When to Call the Doctor**
   - Specific warning signs

Tone: Warm, reassuring, empowering. Use "your baby" language.
Format: Markdown with clear headers
Length: 400-500 words
End with: "Source: CDC Vaccine Information Statement (Public Domain)"

Important: Do NOT quote the source directly. Paraphrase in your own words."""
        
        markdown = self.ask_claude(prompt)
        
        if markdown:
            output_path = self.kb_dir / "vaccines" / f"{vaccine_name.lower().replace(' ', '_')}_vaccine.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"  [OK] Saved to {output_path.name}")
            time.sleep(2)
        else:
            print(f"  [ERROR] Failed to generate content")
    
    # ==================== MILESTONES ====================
    
    def process_milestones(self):
        """Create milestone markdown files from HTML"""
        print("\n[MILESTONES] Processing developmental milestones...")
        
        # Load milestone index
        index_file = self.structured_dir / "milestone_index.json"
        with open(index_file, 'r') as f:
            milestones = json.load(f)
        
        for age_code, data in milestones.items():
            if not data.get('downloaded'):
                print(f"  [SKIP] {data['age_label']} (not downloaded)")
                continue
            
            print(f"  Processing {data['age_label']} milestones...")
            
            html_file = self.raw_dir / f"cdc_milestone_{age_code}.html"
            html_text = self.extract_html_text(html_file)
            
            if not html_text:
                continue
            
            prompt = f"""Using this CDC milestone information for {data['age_label']} old babies, create a parent-friendly milestone guide.

SOURCE TEXT (excerpt):
{html_text[:3000]}

Create a guide with:
1. **{data['age_label']} Developmental Milestones**
2. **What Your Baby Might Be Doing** (organize by category: social, motor, language if clear)
3. **Activities to Try** (3-5 age-appropriate suggestions)
4. **When to Talk to Your Doctor** (concerning signs, but not fear-mongering)

Include somewhere: "Remember: Every baby develops at their own pace!"

Format: Markdown
Length: 300-400 words
End with: "Source: CDC 'Learn the Signs. Act Early' Program (Public Domain)"

Paraphrase in your own words."""
            
            markdown = self.ask_claude(prompt)
            
            if markdown:
                output_path = self.kb_dir / "development" / f"{age_code}_milestones.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
                print(f"  [OK] Saved {age_code}_milestones.md")
                time.sleep(2)
            else:
                print(f"  [ERROR] Failed to generate {age_code}")
    
    # ==================== SYMPTOMS ====================
    
    def process_symptom_html(self, html_path: Path, topic_name: str):
        """Convert symptom HTML to parent-friendly markdown"""
        print(f"  Processing {topic_name}...")
        
        html_text = self.extract_html_text(html_path)
        
        if not html_text:
            print(f"  [ERROR] Could not extract text from {html_path}")
            return
        
        prompt = f"""Using this medical information about {topic_name} as reference, create a practical guide for parents.

SOURCE TEXT (excerpt):
{html_text[:3000]}

Create a guide with:
1. **What It Is** (simple definition for babies/toddlers)
2. **Common Causes** (age-appropriate causes)
3. **What You Can Do at Home**
   - Specific, actionable steps
   - Safe home remedies
4. **When to Call the Doctor**
   - Warning signs organized by urgency
5. **Prevention Tips** (if applicable)

Tone: Empathetic, practical, not scary
Format: Markdown with clear headers
Length: 350-450 words
End with: "Source: MedlinePlus/NIH (Public Domain). Always consult your pediatrician."

Important: Paraphrase in your own words, do not quote directly."""
        
        markdown = self.ask_claude(prompt)
        
        if markdown:
            topic_slug = topic_name.lower().replace(' ', '_')
            output_path = self.kb_dir / "symptoms" / f"{topic_slug}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"  [OK] Saved to {output_path.name}")
            time.sleep(2)
        else:
            print(f"  [ERROR] Failed to generate content")
    
    # ==================== ACTIVITIES ====================
    
    def create_activity_guides(self):
        """Create activity guides from JSON data"""
        print("\n[ACTIVITIES] Creating activity guides...")
        
        # Load activities data
        activities_file = self.structured_dir / "activities_by_age.json"
        with open(activities_file, 'r') as f:
            activities = json.load(f)
        
        activity_types = ["swimming", "music", "gym", "sports", "dance"]
        
        for activity_type in activity_types:
            print(f"  Creating {activity_type} guide...")
            
            # Gather all age ranges for this activity
            activity_data = {}
            for age_range, activities_dict in activities.items():
                if activity_type in activities_dict:
                    activity_data[age_range] = activities_dict[activity_type]
            
            if not activity_data:
                print(f"  [SKIP] No data for {activity_type}")
                continue
            
            prompt = f"""Using this data about {activity_type} classes by age, create a comprehensive guide for parents.

DATA:
{json.dumps(activity_data, indent=2)}

Create a guide with:
1. **Why {activity_type.title()} for Kids?** (2-3 benefits)
2. **When to Start** (age recommendations)
3. **What to Expect by Age**
   - Break down by age ranges
   - What skills they'll learn
4. **Finding Classes**
   - What to look for
   - Typical costs
5. **Tips for Success** (2-3 practical tips)

Tone: Encouraging, informative, practical
Format: Markdown
Length: 400-500 words

Write in your own engaging style."""
            
            markdown = self.ask_claude(prompt)
            
            if markdown:
                output_path = self.kb_dir / "activities" / f"{activity_type}_classes.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
                print(f"  [OK] Saved {activity_type} guide")
                time.sleep(2)
    
    # ==================== PRESCHOOL ====================
    
    def create_preschool_guides(self):
        """Create preschool selection and application guides"""
        print("\n[PRESCHOOL] Creating preschool guides...")
        
        # Load preschool data
        preschool_file = self.structured_dir / "preschool_guide.json"
        with open(preschool_file, 'r') as f:
            preschool_data = json.load(f)
        
        # Guide 1: Preschool Selection
        print("  Creating preschool selection guide...")
        
        prompt = f"""Using this preschool information, create a comprehensive guide for parents choosing a preschool.

DATA:
{json.dumps(preschool_data, indent=2)}

Create a guide with:
1. **When to Start Looking** (timeline)
2. **Types of Preschools**
   - Public vs Private
   - Different philosophies (Montessori, Reggio Emilia, etc.)
3. **What to Look For**
   - Key criteria
   - Questions to ask on tours
4. **The Application Process**
   - Timeline
   - Documents needed
5. **Making Your Decision** (factors to weigh)

Tone: Helpful, comprehensive, not overwhelming
Format: Markdown
Length: 600-700 words

Write as a knowledgeable friend guiding them."""
        
        markdown = self.ask_claude(prompt, max_tokens=3000)
        
        if markdown:
            output_path = self.kb_dir / "education" / "preschool_selection_guide.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"  [OK] Saved preschool selection guide")
            time.sleep(2)
        
        # Guide 2: Preschool Tours
        print("  Creating preschool tour guide...")
        
        prompt2 = """Create a practical guide for parents preparing for preschool tours.

Create a guide with:
1. **Before the Tour**
   - How to schedule
   - What to bring
   - Questions to prepare
2. **During the Tour - What to Observe**
   - Teacher interactions
   - Classroom environment
   - Safety considerations
   - Curriculum approach
3. **Questions to Ask**
   - 15-20 important questions organized by category
4. **Red Flags to Watch For**
   - Warning signs
5. **After the Tour**
   - How to evaluate
   - Taking notes

Tone: Practical, empowering
Format: Markdown with clear sections
Length: 500-600 words"""
        
        markdown2 = self.ask_claude(prompt2, max_tokens=3000)
        
        if markdown2:
            output_path = self.kb_dir / "education" / "preschool_tour_guide.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown2)
            
            print(f"  [OK] Saved preschool tour guide")
            time.sleep(2)
        
        # Guide 3: Kindergarten Registration
        print("  Creating kindergarten registration guide...")
        
        prompt3 = """Create a guide for parents navigating kindergarten registration.

Create a guide with:
1. **When to Register** (typical timeline)
2. **Age Requirements** (cutoff dates vary by state)
3. **Documents You'll Need**
   - Checklist
4. **Kindergarten Readiness**
   - Skills kids should have
   - How to prepare
5. **The Registration Process**
   - Step by step
6. **What Happens Next**
   - School assignments
   - Orientation

Tone: Clear, organized, helpful
Format: Markdown
Length: 400-500 words"""
        
        markdown3 = self.ask_claude(prompt3)
        
        if markdown3:
            output_path = self.kb_dir / "education" / "kindergarten_registration.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown3)
            
            print(f"  [OK] Saved kindergarten guide")
            time.sleep(2)
    
    def run_all(self):
        """Process all data"""
        print("=" * 60)
        print("STARTING DATA PROCESSING WITH AI")
        print("Creating parent-friendly knowledge base")
        print("=" * 60)
        print("\nThis will take 30-40 minutes...")
        print("Using Claude API to create high-quality content\n")
        
        start_time = time.time()
        
        # Process pregnancy content
        print("\n[PREGNANCY] Processing pregnancy guides...")
        pregnancy_weeks = [14, 20, 24, 27, 32, 36, 38]
        for week in pregnancy_weeks:
            html_file = self.raw_dir / f"pregnancy_week_{week}.html"
            if html_file.exists():
                self.process_pregnancy_week(html_file, week)
        
        self.process_pregnancy_vaccines()
        self.create_pregnancy_shopping_guide()
        
        # Process vaccine PDFs
        print("\n[VACCINES] Processing vaccine information...")
        vaccine_pdfs = list(self.raw_dir.glob("vis_*.pdf"))
        for pdf_path in vaccine_pdfs:
            vaccine_name = pdf_path.stem.replace("vis_", "").replace("_", " ").upper()
            self.process_vaccine_pdf(pdf_path, vaccine_name)
        
        # Process symptom HTMLs
        print("\n[SYMPTOMS] Processing symptom information...")
        symptom_htmls = list(self.raw_dir.glob("medlineplus_*.html"))
        for html_path in symptom_htmls:
            topic_name = html_path.stem.replace("medlineplus_", "").replace("_", " ").title()
            self.process_symptom_html(html_path, topic_name)
        
        # Process milestones
        self.process_milestones()
        
        # Create activity guides
        self.create_activity_guides()
        
        # Create preschool guides
        self.create_preschool_guides()
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"DATA PROCESSING COMPLETE ({elapsed/60:.1f} minutes)")
        print("=" * 60)
        
        # Summary
        pregnancy_files = list((self.kb_dir / "pregnancy").glob("*.md")) if (self.kb_dir / "pregnancy").exists() else []
        vaccine_files = list((self.kb_dir / "vaccines").glob("*.md")) if (self.kb_dir / "vaccines").exists() else []
        symptom_files = list((self.kb_dir / "symptoms").glob("*.md")) if (self.kb_dir / "symptoms").exists() else []
        milestone_files = list((self.kb_dir / "development").glob("*.md")) if (self.kb_dir / "development").exists() else []
        activity_files = list((self.kb_dir / "activities").glob("*.md")) if (self.kb_dir / "activities").exists() else []
        education_files = list((self.kb_dir / "education").glob("*.md")) if (self.kb_dir / "education").exists() else []
        
        print(f"\nKnowledge Base Created:")
        print(f"  - Pregnancy guides: {len(pregnancy_files)}")
        print(f"  - Vaccine guides: {len(vaccine_files)}")
        print(f"  - Symptom guides: {len(symptom_files)}")
        print(f"  - Milestone guides: {len(milestone_files)}")
        print(f"  - Activity guides: {len(activity_files)}")
        print(f"  - Education guides: {len(education_files)}")
        print(f"  - Total documents: {len(pregnancy_files) + len(vaccine_files) + len(symptom_files) + len(milestone_files) + len(activity_files) + len(education_files)}")
        
        print("\n[SUCCESS] Ready for Day 3: Create Vector Embeddings!")


def main():
    processor = EnhancedDataProcessor()
    processor.run_all()


if __name__ == "__main__":
    main()