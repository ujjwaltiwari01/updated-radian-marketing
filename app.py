# Radian Marketing Cold Email Automation
# This script automates the process of generating and sending personalized cold emails

import streamlit as st
import pandas as pd
import time
import openai
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import email_validator
import os
import requests
from bs4 import BeautifulSoup

# ----------------------------
# 🔑 YOUR API KEYS
# ----------------------------
# For local development, load .env (optional, not needed on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
import os

def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
BREVO_API_KEY = get_secret("BREVO_API_KEY")
SENDER_NAME = get_secret("SENDER_NAME")
SENDER_EMAIL = get_secret("SENDER_EMAIL")
HUBSPOT_TOKEN = get_secret("HUBSPOT_TOKEN")

openai.api_key = OPENAI_API_KEY

config = sib_api_v3_sdk.Configuration()
config.api_key['api-key'] = BREVO_API_KEY
email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))



# ----------------------------
# 📬 Email Validation
# ----------------------------
def is_valid_email_address(email):
    try:
        if isinstance(email, bytes):
            email = email.decode("utf-8")
        email_validator.validate_email(email)
        return True
    except email_validator.EmailNotValidError:
        return False

def is_role_based_email(email):
    role_keywords = ["info", "support", "admin", "contact", "sales", "team", "hello"]
    local_part = email.split("@")[0].lower()
    return any(local_part.startswith(role) for role in role_keywords)

# ----------------------------
# 🌐 Website Scraping for Personalization
# ----------------------------
def scrape_website_info(website_url):
    """Scrape website title and meta description for personalization."""
    try:
        resp = requests.get(website_url, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()
        return title, meta_desc
    except Exception as e:
        return "", ""

# ----------------------------
# ✍️ Email Generation
# ----------------------------
def generate_email(company, website, keywords):
    # Now this works!
    title, meta_desc = scrape_website_info(website)
    website_info = f"Website Title: {title}\nMeta Description: {meta_desc}" if (title or meta_desc) else "No website info found."
    prompt = f"""
You are an elite, world-renowned B2B cold email strategist and prompt engineer, with mastery in digital marketing psychology, advanced copywriting, and LinkedIn growth. Your output must be at the absolute cutting edge of personalization, creativity, and human resonance.

**MISSION:**  
Craft a cold email for Radian Marketing (Delhi’s top digital marketing agency, now focused EXCLUSIVELY on LinkedIn Management Services for B2B, B2C, and ecommerce clients) that is so unique, so tailored, and so compelling that the recipient feels it was written just for them—by a true expert who deeply understands their business and LinkedIn challenges.

**SUBJECT LINE (CRITICAL):**
- Invent a subject line that is *never generic, never repeated, and never uses the word "Elevate"*.
- The subject must be ultra-creative, hyper-relevant, and spark instant curiosity—something the recipient has never seen before.
- Use advanced personalization: reference their business, website, or a unique insight from their online presence.
- Avoid all clichés, salesy phrases, or anything that could appear in a mass campaign.
- Examples of the right direction (DO NOT COPY):  
  - “{company}’s Next LinkedIn Breakthrough?”  
  - “A Quick Thought After Visiting {website}”  
  - “What Most {company} Competitors Miss on LinkedIn”  
  - “Saw This on Your Site—Had to Reach Out”  
  - “A LinkedIn Idea for {company}’s Growth”  
- The subject must be so intriguing and relevant that the recipient *cannot ignore it*.

**EMAIL BODY:**
- Maximum 7 sentences, each one purposeful and impactful.
- Open with a hyper-specific, genuine compliment or observation about their website, mission, product, or recent campaign (use scraped info if available).
- Reference their business type (e.g., SaaS, D2C, real estate, etc.) and adapt the tone accordingly.
- If possible, mention something about their LinkedIn presence or a recent post/activity.
- Identify a nuanced, realistic LinkedIn challenge they likely face (e.g., inconsistent posting, missed inbound leads, underused company page, weak founder branding).
- Briefly highlight the opportunity cost or what this challenge is costing them (missed connections, lost authority, slower growth).
- Introduce Radian as the trusted LinkedIn partner, sharing a quick, impressive, and *specific* result or social proof (e.g., “We helped [X] founder triple their inbound leads in 90 days…”).
- Offer a soft, no-pressure CTA: invite a short call, offer to share a custom LinkedIn audit, or suggest a relevant insight (“Would it be helpful to see what’s working for similar brands?”).
- End with: Looking forward, Bhaskar

**FORMATTING & RULES:**
- Output ONLY the subject line and email body (no extra commentary).
- Short paragraphs (1–2 sentences each), max 7 sentences total.
- No emojis, ALL CAPS, hype, or filler.
- No overexplaining—be lean, warm, and strategic.
- The reader should feel seen, understood, and genuinely helped—not pitched.
- Use advanced psychological triggers: subtle social proof, FOMO, reciprocity, and curiosity—without pressure.

**GOAL:**  
The recipient should think: “This is for me. This person truly gets my LinkedIn struggle. They’ve helped others like me. I want to reply.”

Company: {company}
Website: {website}
Keywords: {keywords}
Website Info (scraped): {website_info}

Email Format:
Subject: <short, ultra-personalized, curiosity-driven subject>
Body:
- 1st: Hyper-specific appreciation hook
- 2nd: Identify a nuanced LinkedIn challenge
- 3rd: Amplify the opportunity cost
- 4th: Introduce Radian as the LinkedIn solution with specific proof
- 5th: Soft, relevant CTA
- 6th: Sign-off ("Looking forward,\nBhaskar")
"""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700,
    )
    result = response.choices[0].message.content.strip()

    # Extract subject and body, ensuring subject is not duplicated in the body
    subject = ""
    body = ""
    lines = result.splitlines()
    found_subject = False
    found_body = False
    body_lines = []

    for line in lines:
        if not found_subject and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            found_subject = True
        elif line.lower().startswith("body:"):
            found_body = True
            continue  # skip the "Body:" line itself
        elif found_body:
            body_lines.append(line)

    # If subject/body not found, fallback to defaults
    if not subject:
        subject = "AI Outreach That Converts"
    if not body_lines:
        # fallback: use everything except subject line
        body_lines = [l for l in lines if not l.lower().startswith("subject:") and not l.lower().startswith("body:")]

    body = "\n".join(body_lines).strip()

    # Remove subject line if it accidentally appears at the top of the body
    if body.lower().startswith(subject.lower()):
        body = body[len(subject):].lstrip(" :\n")

    if "stop" not in body.lower():
        body += "\n\nIf this isn't for you, just reply STOP."

    return subject, body

    if "stop" not in body.lower():
        body += "\n\nIf this isn't for you, just reply STOP."

    return subject, body

def generate_followup_email(company, website, keywords, prev_subject, prev_body):
    # Scrape website info for personalization
    title, meta_desc = scrape_website_info(website)
    website_info = f"Website Title: {title}\nMeta Description: {meta_desc}" if (title or meta_desc) else "No website info found."

    prompt = f"""
You are an expert B2B email strategist. Write a highly human, attractive, and ultra-personalized follow-up cold email for Radian Marketing, which now provides ONLY LinkedIn Management Services.

**Instructions:**
- The subject line must be creative, human, curiosity-driven, and instantly attention-grabbing—avoid generic or salesy phrases.
- The email body must be quick to read (max 6 sentences), deeply personalized, and feel like it was written just for the recipient.
- Use a warm, peer-to-peer B2B tone—never robotic, hypey, or pushy.
- Reference the previous outreach (subject: "{prev_subject}"), show genuine interest, and offer a new value or insight based on their website or business.
- Personalize using any relevant info from their website.
- Focus ONLY on LinkedIn Management Services (profile optimization, content, outreach, analytics, branding, company page growth, etc.).
- Avoid sounding desperate; keep it friendly, helpful, and results-focused.

Company: {company}
Website: {website}
Keywords: {keywords}
Website Info (scraped): {website_info}
Previous Email Body: {prev_body}

**Email Format:**
Subject: <short, human, curiosity-driven subject>
Body:
- 1st: Reference previous email and express continued interest
- 2nd: Add a new insight, value, or question based on their business/website
- 3rd: Briefly highlight a LinkedIn challenge or opportunity relevant to them
- 4th: Soft CTA (invite to connect, offer value, etc.)
- 5th: Sign-off ("Looking forward,\nBhaskar")

**Rules:**
- No emojis, ALL CAPS, or hype language.
- Short paragraphs (1–2 sentences each).
- The reader should feel seen, understood, and helped—not pitched.
"""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700,
    )
    result = response.choices[0].message.content.strip()

    # Extract subject and body
    subject = ""
    body = ""
    lines = result.splitlines()
    found_subject = False
    found_body = False
    body_lines = []

    for line in lines:
        if not found_subject and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            found_subject = True
        elif line.lower().startswith("body:"):
            found_body = True
            continue
        elif found_body:
            body_lines.append(line)

    if not subject:
        subject = "Quick Follow-up: Radian Marketing"
    if not body_lines:
        body_lines = [l for l in lines if not l.lower().startswith("subject:") and not l.lower().startswith("body:")]

    body = "\n".join(body_lines).strip()

    if body.lower().startswith(subject.lower()):
        body = body[len(subject):].lstrip(" :\n")

    if "stop" not in body.lower():
        body += "\n\nIf this isn't for you, just reply STOP."

    return subject, body

# ----------------------------
# 📤 Send Email
# ----------------------------
def send_email(to_email, to_name, subject, body):
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email, "name": to_name}],
        sender={"email": SENDER_EMAIL, "name": SENDER_NAME},
        subject=subject,
        html_content=body.replace("\n", "<br>")
    )
    return email_api.send_transac_email(email_data)

def upsert_hubspot_contact(email, firstname, lastname, company, website, keywords):
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": {
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "company": company,
            "website": website
            # "notes": keywords  # <-- REMOVE THIS LINE
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 409:  # Contact exists, update it
        # Find contact ID
        search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        search_data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }]
        }
        search_resp = requests.post(search_url, headers=headers, json=search_data)
        if search_resp.ok:
            results = search_resp.json().get("results", [])
            if results:
                contact_id = results[0]["id"]
                update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
                requests.patch(update_url, headers=headers, json={"properties": data["properties"]})
    return response

def add_hubspot_note(email, subject, body):
    # Find contact by email
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    search_data = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }
    search_resp = requests.post(search_url, headers=headers, json=search_data)
    if search_resp.ok:
        results = search_resp.json().get("results", [])
        if results:
            contact_id = results[0]["id"]
            # Create note with correct association structure
            note_url = "https://api.hubapi.com/crm/v3/objects/notes"
            note_data = {
                "properties": {
                    "hs_note_body": f"Subject: {subject}\n\n{body}"
                },
                "associations": {
                    "contactIds": [contact_id]
                }
            }
            note_resp = requests.post(note_url, headers=headers, json=note_data)
            if not note_resp.ok:
                print("Failed to create note:", note_resp.status_code, note_resp.text)
            else:
                print("Note created:", note_resp.json())
        else:
            print("Contact not found for note association.")
    else:
        print("Failed to search contact for note:", search_resp.status_code, search_resp.text)

# ----------------------------
# 🖥️ Streamlit UI
# ----------------------------
st.set_page_config(page_title="Radian Marketing Outreach", layout="wide")
st.title("📬 Radian Marketing: Cold Email Automation")
st.markdown("Upload your lead CSV and let AI generate and send personalized cold emails.")

file = st.file_uploader("📁 Upload CSV (with columns: co_name, website, email, keywords, Name)", type="csv")

if file:
    df = pd.read_csv(file)
    st.success(f"Loaded {len(df)} leads from file.")

    start = st.number_input("Start index", 0, len(df)-1, value=0)
    end = st.number_input("End index", start+1, len(df), value=min(len(df), start+10))

    if st.button("🚀 Start Sending Emails"):
        skipped = []
        for i in range(start, end):
            row = df.iloc[i]
            company = str(row.get("co_name", "")).strip()
            website = str(row.get("website", "")).strip()
            email = str(row.get("email", "")).strip()
            keywords = str(row.get("keywords", "")).strip()
            name = str(row.get("Name", company)).strip()

            # Only skip if email is missing or invalid
            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            st.markdown(f"#### ✉️ Sending to {name} ({email})")

            try:
                subject, body = generate_email(company, website, keywords)
                st.code(f"Subject: {subject}", language="text")
                st.code(body, language="markdown")

                send_email(email, name, subject, body)

                # --- HubSpot Integration ---
                first_name = name.split()[0] if name else ""
                last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
                upsert_hubspot_contact(email, first_name, last_name, company, website, keywords)
                add_hubspot_note(email, subject, body)
                # --- End HubSpot Integration ---

                st.success(f"✅ Sent to {email}")
            except ApiException as e:
                st.error(f"❌ Brevo API Error: {e}")
                skipped.append((i, email, "Brevo error"))
            except Exception as e:
                st.error(f"❌ AI/General Error: {e}")
                skipped.append((i, email, "General error"))

            time.sleep(1.5)  # avoid rate limits

        st.balloons()
        st.success("✅ All emails processed!")

        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
    if st.button("🔁 Send Follow-up Emails"):
        skipped = []
        for i in range(start, end):
            row = df.iloc[i]
            company = str(row.get("co_name", "")).strip()
            website = str(row.get("website", "")).strip()
            email = str(row.get("email", "")).strip()
            keywords = str(row.get("keywords", "")).strip()
            name = str(row.get("Name", company)).strip()

            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            st.markdown(f"#### 🔁 Sending follow-up to {name} ({email})")

            try:
                # Generate the original email to use as context for the follow-up
                prev_subject, prev_body = generate_email(company, website, keywords)
                subject, body = generate_followup_email(company, website, keywords, prev_subject, prev_body)
                st.code(f"Subject: {subject}", language="text")
                st.code(body, language="markdown")

                send_email(email, name, subject, body)
                upsert_hubspot_contact(email, name, "", company, website, keywords)  # Add contact to HubSpot
                add_hubspot_note(email, subject, body)  # Add note in HubSpot
                st.success(f"✅ Follow-up sent to {email}")
            except ApiException as e:
                st.error(f"❌ Brevo API Error: {e}")
                skipped.append((i, email, "Brevo error"))
            except Exception as e:
                st.error(f"❌ AI/General Error: {e}")
                skipped.append((i, email, "General error"))

            time.sleep(1.5)  # avoid rate limits

        st.balloons()
        st.success("✅ All follow-up emails processed!")

        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
else:
    st.info("Please upload a CSV to begin.")