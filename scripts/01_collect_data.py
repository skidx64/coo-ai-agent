"""
Enhanced Data Collection Script - Pregnancy through Age 5
Collects: Pregnancy guides, vaccines, milestones, activities, schools
Windows-compatible (no emoji characters)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict
import PyPDF2
from io import BytesIO

class EnhancedDataCollector:
    """Collects comprehensive parenting data from pregnancy through age 5"""
    
    def __init__(self):
        self.raw_dir = Path("data/raw")
        self.structured_dir = Path("data/structured")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.structured_dir.mkdir(parents=True, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Educational Research Bot - Hackathon Project'
        }
    
    def download_file(self, url: str, filename: str):
        """Download a file from URL"""
        try:
            print(f"  Downloading {filename}...")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            filepath = self.raw_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"  [OK] Saved {filename}")
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to download {filename}: {e}")
            return False
    
    def scrape_url(self, url: str, filename: str):
        """Scrape HTML from URL"""
        try:
            print(f"  Fetching {filename}...")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            filepath = self.raw_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"  [OK] Saved {filename}")
            return True
        except Exception as e:
            print(f"  [ERROR] Failed to fetch {filename}: {e}")
            return False
    
    # ==================== PREGNANCY DATA ====================
    
    def scrape_pregnancy_guides(self):
        """Scrape pregnancy week-by-week guides"""
        print("\n[PREGNANCY] Scraping pregnancy guides...")
        
        # Key weeks in trimester 2 & 3
        key_weeks = [14, 20, 24, 27, 32, 36, 38]
        
        for week in key_weeks:
            url = f"https://www.babycenter.com/pregnancy/week-by-week/{week}-weeks-pregnant"
            filename = f"pregnancy_week_{week}.html"
            self.scrape_url(url, filename)
            time.sleep(2)
    
    def download_pregnancy_vaccines(self):
        """Download pregnancy vaccine information"""
        print("\n[VACCINES] Downloading pregnancy vaccine information...")

        # CDC pregnancy vaccine page (UPDATED 2025)
        url = "https://www.cdc.gov/vaccines-pregnancy/hcp/vaccination-guidelines/index.html"
        filename = "pregnancy_vaccines_cdc.html"
        self.scrape_url(url, filename)
        time.sleep(2)
        
        # Tdap specific info
        url_tdap = "https://www.cdc.gov/pertussis/pregnant/index.html"
        filename_tdap = "pregnancy_vaccine_tdap.html"
        self.scrape_url(url_tdap, filename_tdap)
        time.sleep(2)
    
    def create_pregnancy_timeline(self):
        """Create pregnancy milestone timeline"""
        print("\n[TIMELINE] Creating pregnancy timeline...")
        
        timeline = {
            "trimester_2": {
                "weeks": "14-27",
                "key_milestones": {
                    "week_14": {
                        "mom": "Welcome to 2nd trimester",
                        "baby": "Size of lemon, facial features forming",
                        "to_do": ["Start planning nursery"],
                        "purchases": []
                    },
                    "week_20": {
                        "mom": "Anatomy scan due",
                        "baby": "Halfway point, can hear sounds",
                        "to_do": ["Schedule anatomy scan", "Start shopping for essentials"],
                        "purchases": ["Crib", "Car seat", "Stroller"]
                    },
                    "week_24": {
                        "mom": "Glucose screening test",
                        "baby": "Developing sleep patterns",
                        "to_do": ["Nursery planning", "Register for childbirth classes"],
                        "purchases": ["Changing table", "Dresser", "Rocker"]
                    },
                    "week_27": {
                        "mom": "Tdap vaccine due",
                        "baby": "Can respond to sounds and light",
                        "to_do": ["Get Tdap vaccine", "Start childbirth classes"],
                        "purchases": []
                    }
                }
            },
            "trimester_3": {
                "weeks": "28-40",
                "key_milestones": {
                    "week_32": {
                        "mom": "Weekly checkups begin soon",
                        "baby": "Gaining weight rapidly",
                        "to_do": ["Pack hospital bag", "Install car seat", "Final purchases"],
                        "purchases": ["Newborn clothes", "Diapers", "Bottles", "Nursing supplies"]
                    },
                    "week_36": {
                        "mom": "Group B strep test",
                        "baby": "Full term approaching",
                        "to_do": ["Finalize birth plan", "Pre-register at hospital"],
                        "purchases": []
                    },
                    "week_38": {
                        "mom": "Baby could come any day",
                        "baby": "Ready for birth",
                        "to_do": ["Watch for labor signs", "Keep phone charged", "Have bags ready"],
                        "purchases": []
                    }
                }
            }
        }
        
        timeline_file = self.structured_dir / "pregnancy_timeline.json"
        with open(timeline_file, 'w') as f:
            json.dump(timeline, f, indent=2)
        
        print(f"  [OK] Saved to {timeline_file}")
    
    def create_purchase_timeline(self):
        """Create what-to-buy timeline"""
        print("\n[PURCHASES] Creating purchase timeline...")
        
        purchases = {
            "trimester_2": {
                "weeks": "14-27",
                "big_purchases": [
                    {
                        "item": "Crib",
                        "when": "Week 20-24",
                        "priority": "high",
                        "why": "Needs assembly, delivery delays common",
                        "budget": "$200-800",
                        "safety": "Look for JPMA certification"
                    },
                    {
                        "item": "Car seat",
                        "when": "Week 20-24",
                        "priority": "critical",
                        "why": "Hospital won't release baby without one",
                        "budget": "$150-400",
                        "safety": "Must be rear-facing infant seat"
                    },
                    {
                        "item": "Stroller",
                        "when": "Week 20-28",
                        "priority": "high",
                        "why": "Research takes time, try in store",
                        "budget": "$150-600",
                        "safety": "Check weight limits and brake system"
                    }
                ],
                "optional": [
                    "Changing table",
                    "Glider/rocker",
                    "Dresser",
                    "Baby monitor"
                ]
            },
            "trimester_3": {
                "weeks": "28-40",
                "essentials": [
                    {
                        "category": "Hospital bag",
                        "when": "Week 32-36",
                        "items": [
                            "Newborn outfit for going home",
                            "Blanket",
                            "Car seat (already installed)",
                            "Your insurance card and ID",
                            "Comfortable clothes for you",
                            "Toiletries",
                            "Phone charger"
                        ]
                    },
                    {
                        "category": "Newborn supplies",
                        "when": "Week 32-36",
                        "items": [
                            "Newborn diapers (1-2 packs)",
                            "Wipes",
                            "Diaper cream",
                            "Bottles (if not breastfeeding exclusively)",
                            "Burp cloths",
                            "Swaddles",
                            "Infant nail clippers"
                        ]
                    }
                ]
            },
            "newborn": {
                "age": "0-3 months",
                "can_wait": [
                    "Bouncer seat (after 1 month)",
                    "Play mat (after 2 months)",
                    "Toys (after 2 months)"
                ]
            }
        }
        
        purchases_file = self.structured_dir / "purchase_timeline.json"
        with open(purchases_file, 'w') as f:
            json.dump(purchases, f, indent=2)
        
        print(f"  [OK] Saved to {purchases_file}")
    
    # ==================== BABY VACCINES ====================
    
    def scrape_cdc_milestones(self):
        """Scrape developmental milestones from CDC"""
        print("\n[MILESTONES] Scraping CDC developmental milestones...")
        
        milestones = {}
        
        ages = [
            ("2mo", "2 months", 60),
            ("4mo", "4 months", 120),
            ("6mo", "6 months", 180),
            ("9mo", "9 months", 270),
            ("1yr", "1 year", 365),  # FIXED: Changed from "12 months" to "1 year"
            ("18mo", "18 months", 545),
            ("2yr", "2 years", 730),
            ("3yr", "3 years", 1095),
            ("4yr", "4 years", 1460),
            ("5yr", "5 years", 1825)
        ]
        
        for age_code, age_label, age_days in ages:
            # UPDATED 2025: New CDC Act Early milestone URLs
            url = f"https://www.cdc.gov/act-early/milestones/{age_label.replace(' ', '-').lower()}.html"
            
            try:
                print(f"  Fetching {age_label} milestones...")
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    html_file = self.raw_dir / f"cdc_milestone_{age_code}.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    
                    milestones[age_code] = {
                        "age_label": age_label,
                        "age_days": age_days,
                        "url": url,
                        "downloaded": True
                    }
                    
                    print(f"  [OK] {age_label} milestones saved")
                else:
                    print(f"  [ERROR] Failed to fetch {age_label}: HTTP {response.status_code}")
                    milestones[age_code] = {
                        "age_label": age_label,
                        "age_days": age_days,
                        "downloaded": False
                    }
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  [ERROR] Error fetching {age_label}: {e}")
                milestones[age_code] = {
                    "age_label": age_label,
                    "age_days": age_days,
                    "downloaded": False
                }
        
        milestone_file = self.structured_dir / "milestone_index.json"
        with open(milestone_file, 'w') as f:
            json.dump(milestones, f, indent=2)
        
        print(f"\n[OK] Saved milestone index to {milestone_file}")
        return milestones
    
    def download_vaccine_info(self):
        """Download CDC Vaccine Information Statements (VIS)"""
        print("\n[VACCINES] Downloading CDC Vaccine Information Statements...")

        # UPDATED 2025: New CDC VIS download URLs
        vaccines = [
            ("dtap", "DTaP (Diphtheria, Tetanus, Pertussis)"),
            ("hib", "Hib (Haemophilus influenzae type b)"),
            ("ipv", "IPV (Polio)"),
            ("pcv", "PCV (Pneumococcal)"),
            ("rotavirus", "Rotavirus"),
            ("mmr", "MMR (Measles, Mumps, Rubella)"),
            ("varicella", "Varicella (Chickenpox)"),
            ("hep-b", "Hepatitis B"),
            ("hep-a", "Hepatitis A")
        ]

        for vaccine_code, vaccine_name in vaccines:
            url = f"https://www.cdc.gov/vaccines/hcp/current-vis/downloads/{vaccine_code}.pdf"
            filename = f"vis_{vaccine_code}.pdf"

            print(f"  {vaccine_name}...")
            self.download_file(url, filename)
            time.sleep(1)
    
    def create_vaccine_schedule(self):
        """Create structured vaccine schedule"""
        print("\n[VACCINES] Creating vaccine schedule...")
        
        schedule = {
            "birth": {
                "age_days": 0,
                "age_label": "Birth",
                "vaccines": ["Hepatitis B"],
                "optional": [],
                "notes": "First dose, second dose at 1-2 months"
            },
            "2_months": {
                "age_days": 60,
                "age_label": "2 months",
                "vaccines": ["DTaP", "Hib", "IPV", "PCV13", "RV"],
                "optional": [],
                "notes": "First dose of 5-in-1 series"
            },
            "4_months": {
                "age_days": 120,
                "age_label": "4 months",
                "vaccines": ["DTaP", "Hib", "IPV", "PCV13", "RV"],
                "optional": [],
                "notes": "Second dose of series"
            },
            "6_months": {
                "age_days": 180,
                "age_label": "6 months",
                "vaccines": ["DTaP", "Hib", "PCV13", "RV"],
                "optional": ["Hepatitis B", "IPV", "Influenza"],
                "notes": "Third dose. Flu vaccine can start now."
            },
            "12_months": {
                "age_days": 365,
                "age_label": "12 months",
                "vaccines": ["Hib", "PCV13", "MMR", "Varicella", "Hepatitis A"],
                "optional": [],
                "notes": "Major milestone - MMR and chickenpox vaccines"
            },
            "15_months": {
                "age_days": 455,
                "age_label": "15 months",
                "vaccines": ["DTaP"],
                "optional": [],
                "notes": "Fourth DTaP dose"
            },
            "18_months": {
                "age_days": 545,
                "age_label": "18 months",
                "vaccines": ["Hepatitis A"],
                "optional": [],
                "notes": "Second Hepatitis A dose"
            },
            "4_years": {
                "age_days": 1460,
                "age_label": "4-6 years",
                "vaccines": ["DTaP", "IPV", "MMR", "Varicella"],
                "optional": [],
                "notes": "Before kindergarten boosters"
            }
        }
        
        schedule_file = self.structured_dir / "vaccine_schedule.json"
        with open(schedule_file, 'w') as f:
            json.dump(schedule, f, indent=2)
        
        print(f"  [OK] Saved to {schedule_file}")
    
    # ==================== SYMPTOMS & HEALTH ====================
    
    def scrape_medlineplus_topics(self):
        """Scrape health topics from MedlinePlus (NIH)"""
        print("\n[HEALTH] Scraping MedlinePlus health topics...")

        # UPDATED 2025: Removed unavailable topics (colic, teething, diaperrash)
        topics = [
            ("infantandnewborncare", "Infant and Newborn Care"),
            ("commoncold", "Common Cold"),
            ("fever", "Fever"),
            ("breastfeeding", "Breastfeeding"),
            ("infantandtoddlernutrition", "Infant Nutrition")
        ]
        
        for topic_code, topic_name in topics:
            url = f"https://medlineplus.gov/{topic_code}.html"
            
            try:
                print(f"  Fetching {topic_name}...")
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    html_file = self.raw_dir / f"medlineplus_{topic_code}.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    
                    print(f"  [OK] {topic_name} saved")
                else:
                    print(f"  [ERROR] Failed: HTTP {response.status_code}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  [ERROR] Error: {e}")
    
    # ==================== ACTIVITIES ====================
    
    def create_activities_database(self):
        """Create activities by age database"""
        print("\n[ACTIVITIES] Creating activities database...")
        
        activities = {
            "3-6_months": {
                "swimming": {
                    "ready": True,
                    "class_type": "Parent-baby water bonding",
                    "benefits": ["Motor development", "Bonding", "Water safety intro"],
                    "cost_range": "$20-30 per session",
                    "notes": "Baby must have good head control"
                },
                "music": {
                    "ready": True,
                    "class_type": "Music Together - Baby Class",
                    "benefits": ["Language development", "Sensory stimulation", "Social interaction"],
                    "cost_range": "$100-150 for 10-week session"
                }
            },
            
            "6-12_months": {
                "swimming": {
                    "ready": True,
                    "class_type": "Infant swimming with parent",
                    "focus": "Water comfort, basic kicking",
                    "cost_range": "$25-35 per session"
                },
                "music": {
                    "ready": True,
                    "class_type": "Interactive music classes",
                    "focus": "Instrument exploration, rhythm",
                    "cost_range": "$120-180 for session"
                },
                "sensory_play": {
                    "ready": True,
                    "class_type": "Sensory exploration classes",
                    "benefits": ["Fine motor skills", "Cognitive development"],
                    "cost_range": "$15-25 per drop-in"
                }
            },
            
            "12-24_months": {
                "swimming": {
                    "ready": True,
                    "class_type": "Toddler swimming with parent",
                    "focus": "Independent floating, water safety",
                    "cost_range": "$30-40 per session"
                },
                "gym": {
                    "ready": True,
                    "class_type": "Parent-toddler gymnastics",
                    "benefits": ["Gross motor skills", "Balance", "Coordination"],
                    "cost_range": "$80-120 per month"
                },
                "music": {
                    "ready": True,
                    "class_type": "Toddler music and movement",
                    "focus": "Dancing, instruments, songs",
                    "cost_range": "$100-150 per session"
                }
            },
            
            "2-3_years": {
                "swimming": {
                    "ready": True,
                    "class_type": "Independent toddler classes",
                    "focus": "Basic strokes, water confidence",
                    "cost_range": "$35-45 per session"
                },
                "gym": {
                    "ready": True,
                    "class_type": "Toddler tumbling and gymnastics",
                    "focus": "Strength, coordination, following directions",
                    "cost_range": "$90-130 per month"
                },
                "sports": {
                    "ready": True,
                    "options": ["Soccer Tots", "T-ball introduction"],
                    "benefits": ["Teamwork basics", "Following instructions", "Physical activity"],
                    "cost_range": "$60-100 per season (6-8 weeks)"
                },
                "dance": {
                    "ready": True,
                    "class_type": "Creative movement and dance",
                    "benefits": ["Coordination", "Listening skills", "Self-expression"],
                    "cost_range": "$70-100 per month"
                },
                "daycare_consideration": {
                    "ready": True,
                    "notes": "Many parents consider daycare at this age for socialization",
                    "search_timing": "Start looking 6-12 months before needed"
                }
            },
            
            "3-5_years": {
                "swimming": {
                    "ready": True,
                    "class_type": "Stroke development",
                    "focus": "Freestyle, backstroke basics",
                    "cost_range": "$40-60 per session"
                },
                "gym": {
                    "ready": True,
                    "class_type": "Gymnastics classes",
                    "levels": "Beginner to intermediate",
                    "cost_range": "$100-150 per month"
                },
                "sports": {
                    "ready": True,
                    "options": ["Soccer", "Basketball", "T-ball", "Karate"],
                    "benefits": ["Teamwork", "Discipline", "Physical fitness"],
                    "cost_range": "$80-150 per season"
                },
                "arts": {
                    "ready": True,
                    "options": ["Art classes", "Music lessons", "Dance"],
                    "benefits": ["Creativity", "Fine motor skills", "Self-expression"],
                    "cost_range": "$60-120 per month"
                },
                "stem": {
                    "ready": True,
                    "options": ["Coding for kids", "Science clubs", "Robotics intro"],
                    "benefits": ["Problem-solving", "Logic", "STEM foundation"],
                    "cost_range": "$100-200 per session"
                },
                "preschool": {
                    "ready": True,
                    "search_timing": "Start looking 12-18 months before",
                    "application_season": "Fall/Winter before enrollment year",
                    "notes": "See separate preschool database"
                }
            }
        }
        
        activities_file = self.structured_dir / "activities_by_age.json"
        with open(activities_file, 'w') as f:
            json.dump(activities, f, indent=2)
        
        print(f"  [OK] Saved to {activities_file}")
    
    # ==================== SCHOOLS ====================
    
    def create_preschool_database(self):
        """Create preschool/school database"""
        print("\n[SCHOOLS] Creating preschool database...")
        
        schools = {
            "preschool_search_guide": {
                "when_to_start": "Child age 2.5-3 years, 12-18 months before enrollment",
                "application_season": "Typically Fall/Winter before enrollment year",
                "tour_season": "September-November",
                "decision_timeline": "December-January applications, March-April decisions"
            },
            
            "selection_criteria": [
                "Philosophy (Montessori, Reggio Emilia, Play-based, Academic)",
                "Schedule (Half-day vs Full-day)",
                "Teacher-to-child ratio",
                "Location and commute",
                "Cost and financial aid availability",
                "Curriculum and activities",
                "Outdoor space and facilities",
                "Parent involvement expectations",
                "Wait list length"
            ],
            
            "application_requirements": {
                "common_documents": [
                    "Child's birth certificate",
                    "Immunization records",
                    "Proof of residency",
                    "Parent contact information",
                    "Emergency contacts",
                    "Pediatrician information"
                ],
                "common_questions": [
                    "Is your child potty trained?",
                    "Any special needs or allergies?",
                    "Previous childcare experience?",
                    "Schedule preferences?",
                    "Parent participation availability?"
                ]
            },
            
            "kindergarten_registration": {
                "when_to_start": "Child age 4.5 years, Winter before enrollment",
                "registration_opens": "Typically February 1st",
                "registration_deadline": "Typically March 15th (varies by district)",
                "requirements": [
                    "Child must turn 5 by October 1st (varies by state)",
                    "Birth certificate",
                    "Proof of residency",
                    "Immunization records",
                    "Vision and hearing screening"
                ],
                "readiness_assessment": "Some districts conduct assessments in Spring"
            },
            
            "state_deadlines": {
                "colorado": {
                    "kindergarten_cutoff": "October 1st (must turn 5 by this date)",
                    "registration_period": "February - March",
                    "public_preschool": "Lottery-based, applications in February"
                },
                "note": "Deadlines vary by state and district - always check local requirements"
            }
        }
        
        schools_file = self.structured_dir / "preschool_guide.json"
        with open(schools_file, 'w') as f:
            json.dump(schools, f, indent=2)
        
        print(f"  [OK] Saved to {schools_file}")
    
    def create_mock_resources(self):
        """Create mock local resources data"""
        print("\n[RESOURCES] Creating mock resource data...")
        
        resources = {
            "pediatricians": [
                {
                    "id": 1,
                    "name": "Dr. Sarah Johnson",
                    "practice": "Broomfield Children's Health",
                    "address": "1234 Main St, Broomfield, CO 80020",
                    "phone": "(303) 555-0100",
                    "distance_miles": 1.2,
                    "rating": 4.9,
                    "accepting_new": True,
                    "specialties": ["General Pediatrics", "Newborn Care"]
                },
                {
                    "id": 2,
                    "name": "Dr. Michael Chen",
                    "practice": "Happy Kids Pediatrics",
                    "address": "5678 Oak Ave, Broomfield, CO 80021",
                    "phone": "(303) 555-0200",
                    "distance_miles": 2.5,
                    "rating": 4.7,
                    "accepting_new": False,
                    "specialties": ["General Pediatrics", "ADHD"]
                },
                {
                    "id": 3,
                    "name": "Dr. Emily Rodriguez",
                    "practice": "Sunshine Pediatrics",
                    "address": "789 Elm St, Broomfield, CO 80020",
                    "phone": "(303) 555-0300",
                    "distance_miles": 0.8,
                    "rating": 4.8,
                    "accepting_new": True,
                    "specialties": ["General Pediatrics", "Lactation Support"]
                }
            ],
            
            "daycares": [
                {
                    "id": 1,
                    "name": "Bright Beginnings Learning Center",
                    "address": "123 Learn Lane, Broomfield, CO",
                    "phone": "(303) 555-0400",
                    "distance_miles": 0.5,
                    "rating": 4.8,
                    "ages": "6 weeks - 5 years",
                    "monthly_cost": 1200,
                    "waitlist_months": 2,
                    "philosophy": "Montessori-inspired",
                    "features": [
                        "Organic meals included",
                        "Low teacher-child ratios (1:4 for infants)",
                        "Outdoor play space",
                        "Parent communication app"
                    ]
                },
                {
                    "id": 2,
                    "name": "Little Sprouts Academy",
                    "address": "456 Science St, Broomfield, CO",
                    "phone": "(303) 555-0500",
                    "distance_miles": 0.8,
                    "rating": 4.6,
                    "ages": "3 months - 5 years",
                    "monthly_cost": 1050,
                    "waitlist_months": 0,
                    "philosophy": "STEM-focused",
                    "features": [
                        "Bilingual teachers (Spanish)",
                        "Daily music classes",
                        "STEM activities",
                        "Affordable pricing"
                    ]
                },
                {
                    "id": 3,
                    "name": "Nature Explorers Preschool",
                    "address": "789 Forest Way, Broomfield, CO",
                    "phone": "(303) 555-0600",
                    "distance_miles": 1.2,
                    "rating": 4.9,
                    "ages": "2.5 - 5 years",
                    "monthly_cost": 900,
                    "waitlist_months": 4,
                    "philosophy": "Nature-based learning",
                    "features": [
                        "Outdoor classroom",
                        "Garden program",
                        "Animals on site",
                        "Part-time options"
                    ]
                }
            ],
            
            "classes": {
                "swimming": [
                    {
                        "id": 1,
                        "name": "Goldfish Swim School",
                        "age_range": "4 months - 12 years",
                        "address": "789 Pool Blvd, Broomfield, CO",
                        "phone": "(303) 555-0700",
                        "cost": "$25-35 per session",
                        "schedule": "Multiple times daily",
                        "levels": ["Infant", "Toddler", "Preschool", "School-age"]
                    },
                    {
                        "id": 2,
                        "name": "SafeSplash Swim School",
                        "age_range": "6 months - 14 years",
                        "address": "234 Water St, Broomfield, CO",
                        "phone": "(303) 555-0710",
                        "cost": "$30-40 per session",
                        "schedule": "Weekends and evenings"
                    }
                ],
                
                "music": [
                    {
                        "id": 1,
                        "name": "Music Together",
                        "age_range": "0-5 years",
                        "address": "321 Melody Lane, Broomfield, CO",
                        "phone": "(303) 555-0800",
                        "cost": "$120 for 10-week session",
                        "schedule": "Multiple weekday mornings"
                    }
                ],
                
                "gym": [
                    {
                        "id": 1,
                        "name": "The Little Gym",
                        "age_range": "10 months - 12 years",
                        "address": "567 Tumble St, Broomfield, CO",
                        "phone": "(303) 555-0900",
                        "cost": "$95-130 per month",
                        "schedule": "Multiple days/times",
                        "focus": "Motor skills, confidence, coordination"
                    }
                ]
            },
            
            "preschools": [
                {
                    "id": 1,
                    "name": "Montessori Academy of Broomfield",
                    "type": "private",
                    "philosophy": "Montessori",
                    "ages": "2.5-6 years",
                    "address": "890 Learn Ave, Broomfield, CO",
                    "phone": "(303) 555-1000",
                    "tuition_monthly": 1200,
                    "application_deadline": "December 15 for fall enrollment",
                    "waitlist_typical": "6-12 months",
                    "rating": "4.9/5",
                    "distance_miles": 0.8
                },
                {
                    "id": 2,
                    "name": "Creative Kids Preschool",
                    "type": "private",
                    "philosophy": "Reggio Emilia",
                    "ages": "2-5 years",
                    "address": "456 Art Way, Broomfield, CO",
                    "phone": "(303) 555-1100",
                    "tuition_monthly": 950,
                    "application_deadline": "January 31 for fall enrollment",
                    "features": ["Art-focused", "Outdoor garden", "Parent co-op"],
                    "rating": "4.7/5",
                    "distance_miles": 1.5
                },
                {
                    "id": 3,
                    "name": "Broomfield Heights Elementary PreK",
                    "type": "public",
                    "ages": "4-5 years (must turn 4 by Oct 1)",
                    "address": "1234 School Ave, Broomfield, CO",
                    "phone": "(303) 555-1200",
                    "tuition": "Free",
                    "application_period": "February 1 - March 15",
                    "lottery_date": "March 30",
                    "rating": "8/10 GreatSchools",
                    "distance_miles": 1.2
                }
            ]
        }
        
        resources_file = self.structured_dir / "mock_resources.json"
        with open(resources_file, 'w') as f:
            json.dump(resources, f, indent=2)
        
        print(f"  [OK] Saved to {resources_file}")
    
    def create_milestone_triggers(self):
        """Create milestone-based trigger system"""
        print("\n[TRIGGERS] Creating milestone triggers...")
        
        triggers = {
            "pregnancy": {
                "week_14": {
                    "message_type": "welcome_trimester_2",
                    "priority": "normal"
                },
                "week_20": {
                    "message_type": "anatomy_scan_reminder",
                    "priority": "high",
                    "actions": ["remind_shopping"]
                },
                "week_24": {
                    "message_type": "nursery_planning",
                    "priority": "normal"
                },
                "week_27": {
                    "message_type": "tdap_vaccine",
                    "priority": "high"
                },
                "week_32": {
                    "message_type": "hospital_bag",
                    "priority": "high",
                    "actions": ["final_purchases"]
                },
                "week_36": {
                    "message_type": "labor_prep",
                    "priority": "normal"
                }
            },
            
            "baby_age_days": {
                "0": {
                    "message_type": "congratulations_birth",
                    "priority": "high"
                },
                "7": {
                    "message_type": "first_week_checkin",
                    "priority": "normal"
                },
                "53": {
                    "message_type": "vaccine_reminder_2mo",
                    "priority": "high",
                    "days_before": 7
                },
                "60": {
                    "message_type": "milestone_2mo",
                    "priority": "normal"
                },
                "113": {
                    "message_type": "vaccine_reminder_4mo",
                    "priority": "high",
                    "days_before": 7
                },
                "120": {
                    "message_type": "milestone_4mo",
                    "priority": "normal",
                    "activity_suggestion": "swimming_classes"
                },
                "173": {
                    "message_type": "vaccine_reminder_6mo",
                    "priority": "high",
                    "days_before": 7
                },
                "180": {
                    "message_type": "milestone_6mo",
                    "priority": "normal",
                    "activity_suggestion": "swimming_music"
                },
                "358": {
                    "message_type": "vaccine_reminder_12mo",
                    "priority": "high",
                    "days_before": 7
                },
                "365": {
                    "message_type": "first_birthday",
                    "priority": "high",
                    "activity_suggestion": "gym_classes"
                },
                "545": {
                    "message_type": "milestone_18mo",
                    "priority": "normal"
                },
                "730": {
                    "message_type": "second_birthday",
                    "priority": "normal",
                    "activity_suggestion": "daycare_consideration"
                },
                "912": {
                    "message_type": "preschool_intro",
                    "priority": "normal"
                },
                "1095": {
                    "message_type": "third_birthday",
                    "priority": "normal",
                    "activity_suggestion": "preschool_search"
                },
                "1460": {
                    "message_type": "fourth_birthday",
                    "priority": "normal"
                },
                "1643": {
                    "message_type": "kindergarten_reminder",
                    "priority": "high",
                    "action": "registration_opening"
                }
            },
            
            "seasonal_triggers": {
                "september_preschool_season": {
                    "condition": "child_age_days > 912 AND month == 'September'",
                    "message_type": "preschool_tour_season",
                    "priority": "high"
                },
                "december_application_deadline": {
                    "condition": "child_age_days > 912 AND month == 'December'",
                    "message_type": "preschool_deadline_warning",
                    "priority": "critical"
                },
                "february_kindergarten_registration": {
                    "condition": "child_age_days > 1460 AND month == 'February'",
                    "message_type": "kindergarten_registration_open",
                    "priority": "critical"
                }
            }
        }
        
        triggers_file = self.structured_dir / "milestone_triggers.json"
        with open(triggers_file, 'w') as f:
            json.dump(triggers, f, indent=2)
        
        print(f"  [OK] Saved to {triggers_file}")
    
    def run_all(self):
        """Run all data collection tasks"""
        print("=" * 60)
        print("STARTING ENHANCED DATA COLLECTION FOR COO")
        print("Pregnancy through Age 5 - Comprehensive Parenting Data")
        print("=" * 60)
        print("\nThis will take 20-30 minutes...")
        print("Downloading public domain data from CDC, NIH, and other sources\n")
        
        start_time = time.time()
        
        # Pregnancy data
        self.scrape_pregnancy_guides()
        self.download_pregnancy_vaccines()
        self.create_pregnancy_timeline()
        self.create_purchase_timeline()
        
        # Baby vaccines and milestones
        self.scrape_cdc_milestones()
        self.download_vaccine_info()
        self.create_vaccine_schedule()
        
        # Health topics
        self.scrape_medlineplus_topics()
        
        # Activities
        self.create_activities_database()
        
        # Schools
        self.create_preschool_database()
        
        # Mock resources
        self.create_mock_resources()
        
        # Triggers
        self.create_milestone_triggers()
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"DATA COLLECTION COMPLETE ({elapsed/60:.1f} minutes)")
        print("=" * 60)
        
        # Summary
        raw_files = list(self.raw_dir.glob("*"))
        structured_files = list(self.structured_dir.glob("*"))
        
        print(f"\nFiles collected:")
        print(f"  - Raw files: {len(raw_files)}")
        print(f"  - Structured files: {len(structured_files)}")
        
        print("\nData saved to:")
        print(f"  - Raw data: {self.raw_dir}")
        print(f"  - Structured data: {self.structured_dir}")
        
        print("\n[SUCCESS] Ready for Day 2: Data Processing!")


def main():
    collector = EnhancedDataCollector()
    collector.run_all()


if __name__ == "__main__":
    main()