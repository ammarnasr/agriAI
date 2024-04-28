import streamlit as st  
def main():
    st.header(":mailbox: Get In Touch With Us!")

    # <form action="https://formsubmit.co/asim.awad98@gmail.com" method="POST">

    contact_form = """
    <form action="https://formsubmit.co/a31c8ec03a03a670e12e2b158e8e912e" method="POST">
        <input type="hidden" name="_captcha" value="false">
        <input type="text" name="name" placeholder="Your name" required>
        <input type="email" name="email" placeholder="Your email" required>
        <textarea name="message" placeholder="Your message here"></textarea>
        <button type="submit">Send</button>
    </form>
    """

    st.markdown(contact_form, unsafe_allow_html=True)

    # Use Local CSS File
    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


    local_css("style/style.css")
if __name__ == 'main':
    main()