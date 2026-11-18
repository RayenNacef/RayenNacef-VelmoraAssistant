import re

from velmora.text import expand_negations

REWRITES = [
    #returns and refunds
    (r"\b(send|bring|give|take) (it |them |this |something |an item |the item )?back\b", r"return \2"),
    (r"\b(money back|reimburse\w*|repaid)\b", "refund"),

    #parcels and delivery
    (r"\b(package|packet|shipment)(s?)\b", r"parcel\2"),
    (r"\b(stuck|not moving|no update\w*)\b", "not moved"),
    (r"\b(never arrived|did not arrive|has not arrived|have not arrived|missing)\b", "not received"),
    (r"\b(a|one) week\b", "7 days"),
    (r"\btwo weeks\b", "14 days"),
    (r"\b(a|one) month\b", "30 days"),

    #question about time, like "how long"
    (r"\bhow (fast|quick|quickly|soon)\b", "how long"),

    # account
    (r"\b(log in|sign in|signin|log on|get into)\b", "login"),
    (r"\bprofile\b", "account"),
    (r"\b(can not|do not|could not) remember\b", "forgot"),
    (r"\bforget\b", "forgot"),

    #damage and warranty
    (r"\b(broken|faulty|cracked|smashed|not working|does not work)\b", "damaged"),
    (r"\b(warranty|guarantee)\b", "warranty guarantee"),

    #support
    (r"\b(reply|replies|respond|responds|get back to)\b", "answer"),
    (r"\b(opening|office|business) hours\b", "available"),
    (r"\b(customer service|customer care|help desk|helpdesk)\b", "support"),

    #codes, invoices, newsletter, loyalty
    (r"\b(coupon|discount code|voucher code)(s?)\b", r"promo code\2"),
    (r"\b(receipt|bill)(s?)\b", r"invoice\2"),
    (r"\b(opt out|stop (the |getting )?(emails|newsletters?))\b", "unsubscribe"),
    (r"\b(loyalty|reward) points\b", "loyalty miles"),
    (r"\bback in stock\b", "out of stock back"),
]

COMPILED = [(re.compile(pattern), replacement) for pattern, replacement in REWRITES]


def rewrite_question(question):
    text = expand_negations(question)
    for pattern, replacement in COMPILED:
        text = pattern.sub(replacement, text)
    return " ".join(text.split())
