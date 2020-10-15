import argparse
import mailbox
import bs4

from pprint import pprint


def get_html_text(html):
    try:
        return bs4.BeautifulSoup(html, 'lxml').body.get_text(' ', strip=True)
    except AttributeError: # message contents empty
        return None


class GmailMboxMessage():
    def __init__(self, email_data):
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError('Variable must be type mailbox.mboxMessage')
        self.email_data = email_data

    def parse_email(self):
        email = {}
        email["labels"] = self.email_data['X-Gmail-Labels']
        email["date"] = self.email_data['Date']
        email["from"] = self.email_data['From']
        email["to"] = self.email_data['To']
        email["subject"] = self.email_data['Subject']
        email["text"] = self.read_email_payload()
        return email

    def read_email_payload(self):
        email_payload = self.email_data.get_payload()
        if self.email_data.is_multipart():
            email_messages = list(self._get_email_messages(email_payload))
        else:
            email_messages = [email_payload]
        return [self._read_email_text(msg) for msg in email_messages]

    def _get_email_messages(self, email_payload):
        for msg in email_payload:
            if isinstance(msg, (list,tuple)):
                for submsg in self._get_email_messages(msg):
                    yield submsg
            elif msg.is_multipart():
                for submsg in self._get_email_messages(msg.get_payload()):
                    yield submsg
            else:
                yield msg

    def _read_email_text(self, msg):
        content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
        encoding = 'NA' if isinstance(msg, str) else msg.get('Content-Transfer-Encoding', 'NA')
        if 'text/plain' in content_type and 'base64' not in encoding:
            msg_text = msg.get_payload()
        elif 'text/html' in content_type and 'base64' not in encoding:
            msg_text = get_html_text(msg.get_payload())
        elif content_type == 'NA':
            msg_text = get_html_text(msg)
        else:
            msg_text = None
        return (content_type, encoding, msg_text)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Dump out an mbox file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mbox",
        "-m",
        action="store",
        help="Path to the MBOX file you wish to dump",
        required=True
    )

    args = parser.parse_args()
    return args


def main(args):
    mbx = mailbox.mbox(args.mbox)

    for idx, email_obj in enumerate(mbx):
        email_data = GmailMboxMessage(email_obj)
        eml = email_data.parse_email()
        report = f"Email {idx} from {eml.get('from')} to {eml.get('to')}\n"
        report += f"\t{eml.get('subject')}\n"
        report += f"\t{eml.get('date')}"
        print(report)
        # pprint(eml)


if __name__ == "__main__":
    args = parse_args()
    main(args)
