import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, ".env"))

sys.path.append(BASE_DIR)

from root.models import *
from root.security.mail import *
from root.security.utils import *
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import string
import random
from root.main import app
from root.extensions import db
from root.paystack import Paystack
from root import config

paystack_init = Paystack(config.PAYSTACK_SECRET_KEY)


def generate(n):
    chars = string.ascii_lowercase + string.digits
    random_combination = ''.join(random.choice(chars) for _ in range(n))
    return random_combination


class Script:
    def __init__(self):
        self.base = ""
        self.today = date.today()
        self.admins = None
        self.new_task = None

    def start(self):
        with app.app_context():
            self.initiate_task()
            #self.check_pending_transactions()
            self.remove_unpaid_transactions()
            self.check_queued_subscriptions()
            self.remove_expired_cards()
            self.reset_api()
            self.check_expired_cards()
            self.check_expired_subscriptions()
            self.load_subscription_renewal()

    def initiate_task(self):
        print("Initializing daily task...")
        self.admins = User.query.filter_by(is_superuser=True).all()
        self.new_task = DailyTask.query.filter_by(date=self.today).first()
        if not self.new_task:
            self.new_task = DailyTask(date=self.today)
            db.session.add(self.new_task)
            db.session.commit()

    def check_pending_transactions(self):
        print("Checking pending transaction...")
        trans = Subscription.query.filter_by(status=TransactionStatus.pending).all()
        print(f"Found {len(trans)} pending transaction...")
        for t in trans:
            print(f"Requerying Transaction: {t.reference}...")
            user = t.user
            stat, response = paystack_init.verifyTransaction(t.reference)
            if stat:
                print(f"Requery done: Status: {response['status']}...")
                if t.status.value == response['status']:
                    continue
                t.status = TransactionStatus(response['status'])
                t.details.update({
                    "status": response["status"],
                    "payment_method": response["channel"]
                })
                t.updated = True
                db.session.commit()
                # update successful payment
                if response["status"] == "success":
                    today = date.today()
                    if user.plan.level > 1 and user.expiry_date > today:
                        pass
                    else:
                        user.plan_id = t.plan_id
                        user.plan = t.plan
                        user.duration = t.duration
                        user.start_date = t.date
                        user.expiry_date = t.expiry_date
                        user.total_tokens = t.plan.monthly_token_limit
                        user.tokens_used = 0
                        user.tokens_remaining = t.plan.monthly_token_limit
                        user.last_limit_reset = date.today()
                        user.daily_api_limit = t.plan.daily_api_limit
                        user.daily_api_used = 0
                        user.last_api_reset = date.today()
                        user.daily_token_limit = t.plan.daily_token_limit
                        user.daily_tokens_used = 0
                        user.last_token_reset = date.today()
                        user.expired = False
                        t.applied = True
                        db.session.commit()
                    try:
                        stat2, res = send_sub_payment(user, t)
                        if not stat2:
                            for a in self.admins:
                                error_note = Notification(
                                    user_id=a.id, user=a,
                                    title=f"Email Notification for transaction:{t.reference}", details={
                                        "type": "email_error",
                                        "message": f"An error occurred while sending email notification for Transaction: {response['reference']}.",
                                        "transaction reference": {response["reference"]},
                                        "error details": res
                                    }
                                )
                                db.session.add(error_note)
                                db.session.commit()
                    except Exception as e:
                        for a in self.admins:
                            error_note = Notification(
                                user_id=a.id, user=a,
                                title=f"Email Notification for transaction:{t.reference}", details={
                                    "type": "email_error",
                                    "message": f"An error occurred while sending email notification for Transaction: {response['reference']}.",
                                    "transaction reference": {response["reference"]},
                                    "error details": str(e)
                                }
                            )
                            db.session.add(error_note)
                            db.session.commit()
                    new_note = Notification(
                        user_id=user.id, user=user, title="Subscription Payment", details={
                            "type": "subscription",
                            "message": f"You have successfully made a subscription payment of {response['currency']}{str(t.amount)} for {t.duration}.",
                            "Subscription Plan": f"{t.plan.title} Plan",
                            "Expiry Date": f"{t.expiry_date.strftime('%B %d, %Y')}"
                        }
                    )
                    db.session.add(new_note)
                    db.session.commit()
            else:
                print(f"Error occurred while requerying: {str(response)}")
    def remove_unpaid_transactions(self):
        print("Deleting abandoned transaction...")
        trans = Transaction.query.filter_by(status=TransactionStatus.unpaid).all()
        subs = Subscription.query.filter_by(status=TransactionStatus.unpaid).all()
        for o in trans:
            if self.is_past(o.timestamp.date()):
                db.session.delete(o)
        for p in subs:
            if self.is_past(p.timestamp.date()):
                db.session.delete(p)
        self.new_task.unpaid_transactions = True
        db.session.commit()

    def check_queued_subscriptions(self):
        print("Checking queued subscriptions...")
        subs = Subscription.query.filter_by(status="success", applied=False).all()
        for s in subs:
            user = s.user
            if  user.expiry_date <= self.today:
                user.plan = s.plan
                user.duration = s.duration
                user.start_date = s.date
                user.expiry_date = s.expiry_date
                user.reset_all()
                user.total_tokens = s.plan.monthly_token_limit
                user.tokens_remaining = s.plan.monthly_token_limit
                user.daily_api_limit = s.plan.daily_api_limit
                user.daily_token_limit = s.plan.daily_token_limit
                user.expired = False
                s.applied = True
                db.session.commit()
            else: pass
        self.new_task.queued_subscriptions = True
        db.session.commit()

    def remove_expired_cards(self):
        print("Deleting expired cards...")
        cards = Card.query.filter_by(expired=True)
        for c in cards:
            db.session.delete(c)
        db.session.commit()
        self.new_task.remove_expired_cards = True
        db.session.commit()

    def reset_api(self):
        users = User.query.filter_by(expired=False, is_superuser=False)
        for u in users:
            u.reset_all()
        db.session.commit()
        self.new_task.reset_api = True
        db.session.commit()

    def check_expired_cards(self):
        print("Checking for expired cards...")
        cards = Card.query.filter_by(expired=False)
        curr_year = self.today.year
        curr_month = self.today.month
        for c in cards:
            year = int(c.details["exp_year"])
            month = int(c.details["exp_month"])
            if curr_year > year or (curr_year == year and curr_month > month):
                c.expired = True
                stat, res = send_card_expiration(c)
                if not stat:
                    pass
            db.session.commit()
        self.new_task.check_expired_cards = True
        db.session.commit()

    def check_expired_subscriptions(self):
        users = User.query.filter_by(expired=False, is_superuser=False)
        for u in users:
            if u.plan.level > 1 and u.expiry_date:
                if self.is_today(u.expiry_date) or self.is_past(u.expiry_date):
                    u.expired = True
                    db.session.commit()
                    send_sub_expiration(u)
                elif self.is_tomorrow(u.expiry_date) or self.in_x_weeks(1, u.expiry_date):
                    send_sub_reminder(u)
        self.new_task.check_expired_subs = True
        db.session.commit()

    def load_subscription_renewal(self):
        users = User.query.filter_by(expired=True, is_superuser=False)
        for s in users:
            if s.plan.level > 1 and s.auto_renewal:
                curr_dur = s.duration.split(' ')[0]
                plan = s.plan
                amt_obj = {
                    "1": plan.monthly_price, "3": plan.quarterly_price,
                    "6": plan.biannual_price, "12": plan.annual_price
                }
                amount = amt_obj[curr_dur]
                datem = self.today
                expiry_date = datem + relativedelta(months=int(curr_dur))
                trans = Subscription(
                    user_id=s.id, user=s, plan_id=plan.id, plan=plan, duration=f"{s.duration}",
                    reference=generateReference('sub', 5),
                    amount=amount, date=datem, expiry_date=expiry_date,
                    details={"charges": "0.00", "total_amount": str(amount)},
                    description=f"{s.duration} Subscription for {plan.title} Plan",
                    applied=False, updated=True
                )
                db.session.add(trans)
                db.session.commit()
                cards = s.cards
                if not cards:
                    send_renewal_failure(s, "no linked card")
                else:
                    card = cards[0]
                    if not card.expired:
                        stat, response = paystack_init.chargeAuthorization(
                            email=card.email, amount=f"{trans.amount * 100}",
                            reference=trans.reference, authorization_code=card.authorizationCode
                        )
                        if not stat:
                            for a in self.admins:
                                new_note = Notification(
                                    user_id=a.id, user=a, title=f"Subscription Renewal Error:{trans.reference}", details={
                                        "type": "renewal_error",
                                        "message": f"An error occurred while renewing subscription  forTransaction: {trans.reference}.",
                                        "error details": response
                                    }
                                )
                                db.session.add(new_note)
                                db.session.commit()
                            send_renewal_failure(s, response)
                    else:
                        send_renewal_failure(s, "an expired linked card")

        self.new_task.renew_expired_subs = True
        db.session.commit()

    def is_today(self, n_date):
        return n_date == self.today

    def is_tomorrow(self, n_date):
        return n_date == self.today + timedelta(days=1)

    def is_past(self, n_date):
        return n_date < self.today

    def is_past_month(self, n_date):
        return n_date == date.today() - timedelta(days=30)

    def add_one_day(self):
        date_field = date.today() + timedelta(days=1)
        return date_field

    def in_x_weeks(self, n, n_date):
        date_field = date.today() + timedelta(weeks=n)
        return date_field == n_date

    def add_one_week(self):
        date_field = date.today() + timedelta(weeks=1)
        return date_field

    def add_one_month(self):
        date_field = date.today() + relativedelta(months=1)
        return date_field


if __name__ == "__main__":
    my_plan = Script()
    print("Starting Daily Task....")
    my_plan.start()
    print("Daily task completed successfully!")
