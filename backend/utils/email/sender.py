import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from ..config import get_settings
from ..logger import default_logger as logger

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = self.settings.SMTP_SERVER
        self.smtp_port = 465  # 固定使用465端口，这是QQ邮箱的SSL端口
        self.smtp_user = self.settings.SMTP_USERNAME
        self.smtp_password = self.settings.EMAIL_PASSWORD
        self.sender = self.settings.SMTP_SENDER
    
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        cc_addresses: Optional[List[str]] = None,
        is_html: bool = False
    ) -> bool:
        """
        发送邮件的核心方法
        """
        smtp = None
        send_success = False
        try:
            # 1. 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = f"Robot <{self.sender}>"
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            if cc_addresses:
                msg['Cc'] = ', '.join(cc_addresses)
            
            # 2. 添加邮件内容
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            # 3. 创建SMTP连接
            smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            # 4. 登录
            try:
                smtp.login(self.smtp_user, self.smtp_password)
            except smtplib.SMTPAuthenticationError:
                logger.error("SMTP认证失败，请检查用户名和密码")
                return False
                
            # 5. 发送邮件
            smtp.send_message(msg)
            send_success = True
            logger.info(f"邮件发送成功: {subject} -> {', '.join(to_addresses)}")
            return True

        except Exception as e:
            if not send_success:  # 只在实际发送失败时记录错误
                logger.error(f"邮件发送过程出错: {str(e)}")
            return False
            
        finally:
            # 6. 安全关闭SMTP连接
            if smtp:
                try:
                    smtp.quit()
                except Exception:
                    pass  # 忽略关闭连接时的错误

    async def send_verification_code(self, to_address: str, code: str) -> bool:
        """
        专门用于发送验证码的方法
        """
        subject = "验证码"
        body = f"""
        <div style="padding: 20px; background-color: #f7f7f7; border-radius: 5px;">
            <h2 style="color: #333;">您的验证码</h2>
            <p style="font-size: 16px; color: #666;">您的验证码是：</p>
            <div style="background-color: #fff; padding: 15px; border-radius: 5px; margin: 15px 0; text-align: center;">
                <span style="font-size: 24px; font-weight: bold; color: #333;">{code}</span>
            </div>
            <p style="font-size: 14px; color: #999;">验证码5分钟内有效，请勿泄露给他人。</p>
        </div>
        """
        return await self.send_email(
            to_addresses=[to_address],
            subject=subject,
            body=body,
            is_html=True
        )

# 创建默认邮件发送器实例
email_sender = EmailSender() 