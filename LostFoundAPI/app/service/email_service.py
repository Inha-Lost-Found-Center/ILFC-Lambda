import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_verification_email(to_email: str, code: str) -> bool:
    """
    Gmail SMTP를 사용하여 인증 코드를 전송합니다.
    Returns:
        bool: 전송 성공 여부
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    sender_email = settings.GMAIL_USER
    password = settings.GMAIL_PASSWORD

    subject = "[인하분실물센터] 회원가입 인증번호 안내"

    body = f"""
    <html>
    <head>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        </style>
    </head>
    <body style="font-family: 'Pretendard', 'Malgun Gothic', sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
        
        <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            
            <div style="background-color: #002855; padding: 25px 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 20px; letter-spacing: 1px; font-weight: 700;">
                    INHA LOST & FOUND
                </h1>
                <p style="color: #aaccff; margin: 5px 0 0 0; font-size: 12px;">
                    인하대학교 스마트 분실물 센터
                </p>
            </div>

            <div style="padding: 40px 30px; text-align: center;">
                <h2 style="color: #333333; font-size: 18px; margin-bottom: 20px;">회원가입 인증번호</h2>
                
                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin-bottom: 30px;">
                    안녕하세요.<br>
                    서비스 이용을 위해 아래 인증번호를<br>
                    입력창에 입력해 주세요.
                </p>

                <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 20px; margin-bottom: 30px;">
                    <span style="color: #002855; font-size: 32px; font-weight: 800; letter-spacing: 8px; display: block;">
                        {code}
                    </span>
                </div>

                <p style="color: #888888; font-size: 13px;">
                    인증번호는 <strong>5분간</strong> 유효합니다.<br>
                    본인이 요청하지 않았다면 이 메일을 무시해 주세요.
                </p>
            </div>

            <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #eeeeee;">
                <p style="color: #aaaaaa; font-size: 11px; margin: 0;">
                    © Inha University Lost & Found Center.<br>
                    All rights reserved.
                </p>
            </div>

        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[Email Send Error] {str(e)}")
        return False
