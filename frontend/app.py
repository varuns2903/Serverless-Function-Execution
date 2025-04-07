import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import json
import time
import pytz

API_URL = "http://localhost:8000"

def api_call(method, endpoint, data=None):
    url = f"{API_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        response.raise_for_status()
        return response.json() if response.text else {"status": "success"}
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request Failed: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Serverless Platform", layout="wide")
    st.title("Serverless Function Platform")

    # Sidebar for Navigation
    page = st.sidebar.selectbox("Navigate", ["Deploy Function", "Manage Functions", "Execute Function", "Metrics Dashboard"])

    # Track last visited page to reset form if needed
    if "last_page" not in st.session_state:
        st.session_state.last_page = ""

    if page != st.session_state.last_page:
        st.session_state.pop("loaded_func", None)

    # Deploy Function Page
    if page == "Deploy Function":
        st.header("Deploy a New Function")
        with st.form("deploy_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Function Name", placeholder="e.g., my_function")
                language = st.selectbox("Language", ["python", "javascript"])
            with col2:
                timeout = st.number_input("Timeout (seconds)", min_value=1, value=30)
            code = st.text_area("Code", height=200, placeholder="Enter your code here")
            submit = st.form_submit_button("Deploy")
            if submit:
                if not name or not code:
                    st.error("Function Name and Code are required!")
                else:
                    func = {"name": name, "language": language, "code": code, "timeout": timeout}
                    result = api_call("POST", "/functions/", func)
                    if result:
                        st.success(f"Function {result['id']} deployed successfully!")

    # Manage Functions Page
    elif page == "Manage Functions":
        st.header("Manage Functions")
        funcs = api_call("GET", "/functions/")
        if funcs:
            df = pd.DataFrame(funcs)
            display_columns = ["id", "name", "language", "code", "timeout"]
            st.dataframe(df[display_columns], use_container_width=True)

            if "loaded_func" not in st.session_state:
                st.session_state.loaded_func = None

            func_id = st.number_input("Function ID to Edit/Delete", min_value=1, step=1)

            if st.button("Load Function"):
                func = api_call("GET", f"/functions/{func_id}")
                if func:
                    st.session_state.loaded_func = func
                else:
                    st.warning(f"Function {func_id} not found.")

            if st.session_state.loaded_func:
                func = st.session_state.loaded_func

                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Function Name", value=func["name"])
                        language = st.selectbox(
                            "Language", ["python", "javascript"],
                            index=["python", "javascript"].index(func["language"])
                        )
                    with col2:
                        timeout = st.number_input("Timeout (seconds)", min_value=1, value=func["timeout"])
                    code = st.text_area("Code", value=func["code"], height=200)

                    col3, col4 = st.columns(2)
                    with col3:
                        update_clicked = st.form_submit_button("Update")
                    with col4:
                        delete_clicked = st.form_submit_button("Delete")

                    if update_clicked:
                        updated_func = {
                            "id": func_id,
                            "name": name,
                            "language": language,
                            "code": code,
                            "timeout": timeout
                        }
                        result = api_call("PUT", f"/functions/{func_id}", updated_func)
                        if result:
                            st.success(f"Function {func_id} updated successfully!")
                            st.session_state.loaded_func = None
                            time.sleep(1.5)
                            st.rerun()

                    if delete_clicked:
                        result = api_call("DELETE", f"/functions/{func_id}")
                        if result:
                            st.success(f"Function {func_id} deleted successfully!")
                            st.session_state.loaded_func = None
                            time.sleep(1.5)
                            st.rerun()
        else:
            st.info("No functions available.")

    # Execute Function Page
    elif page == "Execute Function":
        st.header("Execute a Function")
        col1, col2 = st.columns(2)
        with col1:
            func_id = st.number_input("Function ID", min_value=1, step=1)
        with col2:
            payload = st.text_area("Payload (JSON)", "{}", height=100)
        if st.button("Execute"):
            try:
                payload_dict = json.loads(payload)
                result = api_call("POST", f"/execute/{func_id}", payload_dict)
                if result:
                    st.subheader("Execution Result")
                    st.code(result["result"], language="text")
            except json.JSONDecodeError:
                st.error("Invalid JSON payload!")

    # Metrics Dashboard Page
    elif page == "Metrics Dashboard":
        st.header("Metrics Dashboard")
        func_id_filter = st.number_input("Filter by Function ID (optional, 0 for all)", min_value=0, step=1, value=0)
        metrics = api_call("GET", "/metrics/" if func_id_filter == 0 else f"/metrics/?func_id={func_id_filter}")
        if metrics:
            df = pd.DataFrame(metrics)
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

                # Convert to IST
                ist = pytz.timezone("Asia/Kolkata")
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert(ist)

                st.write("Metrics Data:", df)
                fig = px.line(df, x="timestamp", y="response_time", color="func_id", 
                              title="Response Time Over Time", labels={"response_time": "Response Time (s)"})
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Statistics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Response Time", f"{df['response_time'].mean():.2f} s")
                col2.metric("Execution Count", len(df))
                col3.metric("Error Rate", f"{(df['errors'].notnull().sum() / len(df) * 100):.1f}%")
            else:
                st.info("No metrics available for this filter.")
        else:
            st.info("No metrics available.")

    # Update last visited page
    st.session_state.last_page = page

if __name__ == "__main__":
    main()
