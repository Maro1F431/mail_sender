import streamlit as st
import streamlit.components.v1 as components
import smtplib
import time
import pandas as pd
from email.message import EmailMessage
import atexit

padding = 0
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} </style> """, unsafe_allow_html=True)

# Hide hamburger button
st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

def logout():
    st.session_state.smtp_client.close()
    print("Good bye !")

def on_login(password):
    try:
        st.session_state.smtp_client.login(st.session_state.email_adress, password)
        st.session_state.logged_in = True
    except:
        st.warning("Could not login, please enter a valid email and password.")

def send_emails(nb_batch, time_between_email, email_subject, emails_list, always_in_copy, progress):
    nb_sent = 0
    nb_to_send = st.session_state.emails.shape[0]
    if nb_to_send > 0:
        with progress:
            progress_bar = st.progress(0)
            txt_remaining_time = st.empty()
            txt_nb_sent = st.empty()
            txt_nb_to_send = st.empty()
            while(st.session_state.emails.shape[0] > 0 and st.session_state.keep_sending == True):

                #Send emails
                msg = EmailMessage()
                msg['Subject'] = email_subject
                msg['From'] = st.session_state.email_adress
                To_list = st.session_state.emails['Emails'].tolist()
                if always_in_copy != '':
                    To_list.append(always_in_copy)
                print(To_list)
                msg['To'] = To_list
                msg.set_content(st.session_state.email_to_send, subtype="html")
                st.session_state.smtp_client.send_message(msg)

                #update variables
                nb_remaining_email = st.session_state.emails.shape[0]
                nb_sent += nb_batch if nb_remaining_email > nb_batch else nb_remaining_email
                remaining_time = ((nb_to_send - nb_sent) / nb_batch) * time_between_email
                st.session_state.emails = st.session_state.emails.tail(-nb_batch)
                st.session_state.emails.reset_index(drop=True, inplace=True)
                emails_list.write(st.session_state.emails)
                
                #time_to_sleep = 60 * time_between_email
                time_to_sleep = time_between_email

                #Progress bar
                progress_bar.progress( nb_sent / nb_to_send)
                txt_remaining_time.write("remaining time :" + str(remaining_time))
                txt_nb_sent.write("number of emails sent: " + str(nb_sent))
                txt_nb_to_send.write("number of emails to send " + str(nb_to_send))

                #Wait for next batch
                while((nb_sent < nb_to_send) and time_to_sleep > 0 and st.session_state.keep_sending == True):
                    time_to_sleep -= 1
                    time.sleep(1)
            time.sleep(2)
            progress_bar.empty()
            txt_remaining_time.empty()
            txt_nb_sent.empty()
            txt_nb_to_send.empty()
    st.session_state.keep_sending = False
    

if 'smtp_client' not in st.session_state:
    st.session_state.smtp_client = smtplib.SMTP_SSL('smtp.gmail.com', 465);

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    atexit.register(logout)

if 'email_adress' not in st.session_state:
    st.session_state.email_adress = ''

if st.session_state.logged_in == False:
    st.session_state.email_adress  = st.text_input("Enter Your Email")
    password  = st.text_input("Enter Your Password", type="password")
    st.button("Login", on_click=on_login, args=(password,))

else:
    if 'emails' not in st.session_state:
        st.session_state.emails = pd.DataFrame(columns=['Emails'])
    if 'keep_sending' not in st.session_state:
        st.session_state.keep_sending = False
    if 'email_to_send' not in st.session_state:
        st.session_state.email_to_send = ''

    col_form, col_email_list = st.columns(2)

    with col_form:
        with st.form("Emails", clear_on_submit=True):
            txt = st.text_area("List of Emails" , height=200, placeholder="One email per line\n" +
            "Example:\n"
            + "juan1@gmail.com\n"
            + "juan2@gmail.com\n"
            + "juan3@gmail.com\n"
            + "etc ...")
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.emails = st.session_state.emails.append(pd.DataFrame(txt.splitlines(), columns=["Emails"]))
                st.session_state.emails.reset_index(drop=True, inplace=True)

    with col_email_list:
        emails_list = st.empty()
        emails_list.write(st.session_state.emails)

    col_html_email, col_preview = st.columns(2)


    with col_html_email:
        with st.form("Upload email to send"):
            email_to_send = st.text_area("Enter HMTL code for Email", height=250)
            submitted = st.form_submit_button("Upload email")
            if submitted:
                st.session_state.email_to_send = email_to_send
    with col_preview:
        st.write("Email preview: ")
        components.html(st.session_state.email_to_send, height=300, scrolling=True)

    with st.form("Send emails"):
        time_between_email = st.number_input("Enter time (in minutes) between emails", 1 , 10, 5, 1)
        nb_email_batch = st.number_input("Enter the number of emails to send each time", 1 , 100, 10, 1)
        email_subject = st.text_input("Email subject")
        always_in_copy = st.text_input("Optional: Email always in copy")
        sub_col, stop_col = st.columns(2)
        progress = st.container()
        with sub_col:
            submitted = st.form_submit_button("SEND EMAILS")
            if submitted:
                st.session_state.keep_sending = True
                send_emails(nb_email_batch, time_between_email, email_subject, emails_list, always_in_copy, progress)
        with stop_col:
            stop_bt = st.form_submit_button("CANCEL")
            if stop_bt:
                st.session_state.keep_sending = False
   
