import streamlit as st
import requests
import plotly.express as px

API_URL = "http://localhost:8000"

def api_call(method, endpoint, data=None):
    url = f"{API_URL}{endpoint}"
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()

def main():
    st.title("Serverless Platform")

    # Function Deployment
    with st.form("deploy"):
        name = st.text_input("Function Name")
        language = st.selectbox("Language", ["python", "javascript"])
        code = st.text_area("Code")
        timeout = st.number_input("Timeout (seconds)", min_value=1, value=30)
        submit = st.form_submit_button("Deploy")
        if submit:
            func = {"name": name, "language": language, "code": code, "timeout": timeout}
            result = api_call("POST", "/functions/", func)
            st.success(f"Function {result['id']} deployed!")

    # Function List
    funcs = api_call("GET", "/functions/")
    st.write("Functions:", funcs)

    # Execute Function
    func_id = st.number_input("Function ID to Execute", min_value=1)
    payload = st.text_area("Payload (JSON)", "{}")
    if st.button("Execute"):
        result = api_call("POST", f"/execute/{func_id}", eval(payload))
        st.write("Result:", result)

    # Metrics Dashboard
    metrics = api_call("GET", "/metrics/")  # Assume API endpoint exists
    if metrics:
        fig = px.line(metrics, x="timestamp", y="response_time", title="Function Metrics")
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()  