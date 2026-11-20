import json
import os
import urllib.request
import urllib.error
import streamlit as st

st.set_page_config(
    page_title="Eligibility Assessment Portal_Raj",
    page_icon="📋",
    layout="centered" 
)

# Configuration for MCP / Workflow Engine
DEFAULT_API_URL = "https://aas-workflow-engine.servicesessentials.ibm.com/api/v1/run/3ae4fcef-7ec8-4269-8e10-319e1430ebb0"
DEFAULT_API_KEY = os.environ.get("AAS_API_KEY", "sk-RwjM_ttkgTft0wfm0fS2feVdcYyJPmAoupCGAVOuj5w")

st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f62fe;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #525252;
        margin-bottom: 1.5rem;
    }
    .result-card-eligible {
        background-color: #defbe6;
        border: 1px solid #24a148;
        border-radius: 8px;
        padding: 18px;
        margin-top: 20px;
    }
    .result-card-ineligible {
        background-color: #fff1f1;
        border: 1px solid #da1e28;
        border-radius: 8px;
        padding: 18px;
        margin-top: 20px;
    }
    .status-badge-eligible {
        display: inline-block;
        background-color: #24a148;
        color: #ffffff;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 4px 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .status-badge-ineligible {
        display: inline-block;
        background-color: #da1e28;
        color: #ffffff;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 4px 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .result-text {
        font-size: 1rem;
        color: #161616;
        white-space: pre-wrap;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Care & Support Eligibility Checker - In the app.py line 73</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Assess applicant eligibility using the automated Agentic Workflow Engine</div>', unsafe_allow_html=True)

def check_eligibility(name: str, age: int, country: str, hours_of_care: int, api_url: str, api_key: str):
    """Calls the workflow engine MCP endpoint to evaluate eligibility."""
    payload = {
        "input_value": f"{name.strip()},{age},{country.strip()},{hours_of_care}",
        "output_type": "chat",
        "input_type": "chat"
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EligibilityChecker/1.0"
    }

    req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_body = response.read().decode("utf-8")
            res_json = json.loads(resp_body)
            
            # Extract output message
            message_text = ""
            try:
                outputs = res_json.get("outputs", [])
                if outputs:
                    first_output = outputs[0].get("outputs", [])
                    if first_output:
                        # Try getting from messages list
                        msgs = first_output[0].get("messages", [])
                        if msgs:
                            message_text = msgs[0].get("message", "")
                        if not message_text:
                            # Fallback to results text
                            results_data = first_output[0].get("results", {}).get("message", {}).get("data", {})
                            message_text = results_data.get("text", "")
            except Exception:
                message_text = str(res_json)

            if not message_text:
                message_text = resp_body

            return True, message_text
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8") if e.fp else str(e)
        return False, f"HTTP Error {e.code}: {e.reason} - {error_msg}"
    except Exception as e:
        return False, f"Connection Error: {str(e)}"

# Input Form
with st.form("eligibility_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Name", value="Rajesh", placeholder="Enter applicant name")
        country = st.selectbox(
            "Country",
            options=["Scotland", "England", "Wales", "Northern Ireland", "Other"],
            index=0
        )
        
    with col2:
        age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
        hours_of_care = st.number_input("Hours of Care", min_value=0, max_value=168, value=45, step=1)

    submitted = st.form_submit_button("Check Eligibility", use_container_width=True, type="primary")

if submitted:
    if not name.strip():
        st.error("Please enter a valid applicant name.")
    else:
        with st.spinner("Connecting to Agentic Workflow MCP Server..."):
            success, result_message = check_eligibility(
                name=name,
                age=int(age),
                country=country,
                hours_of_care=int(hours_of_care),
                api_url=DEFAULT_API_URL,
                api_key=DEFAULT_API_KEY
            )
            
        if success:
            is_eligible = "eligible" in result_message.lower() and "not eligible" not in result_message.lower() and "ineligible" not in result_message.lower()
            
            if is_eligible:
                st.markdown(f"""
                <div class="result-card-eligible">
                    <div class="status-badge-eligible">ELIGIBLE</div>
                    <div class="result-text">{result_message}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-card-ineligible">
                    <div class="status-badge-ineligible">NOT ELIGIBLE</div>
                    <div class="result-text">{result_message}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with st.expander("Submission Details"):
                st.write({
                    "Applicant Name": name,
                    "Age": age,
                    "Country": country,
                    "Hours of Care": hours_of_care,
                    "Evaluated Payload": f"{name},{age},{country},{hours_of_care}"
                })
        else:
            st.error(f"Failed to evaluate eligibility: {result_message}")
