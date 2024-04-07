import json
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from pip._internal.utils import logging

from product.models import Rule
from product.views import get_model_by_item_type
from user.models import User
from utils.emailSend import send_custom_email
from utils.redis_connect import redis_client

logger = logging.getLogger(__name__)

user_redis_pre = 'fatigue:id:'


def browse_notify_callback(ch, method, properties, body):
    try:
        logger.info("Received message from Flink Order Browse Notify :" + body.decode())
        parsed_data = json.loads(body.decode())
        rule_id = parsed_data.get("ruleId")
        time = parsed_data.get("time")
        user_id = parsed_data.get("userId")

        try:
            # 尝试根据rule_id获取Rule实例
            rule_instance = Rule.objects.get(id=rule_id)
            user_instance = User.objects.get(id=user_id)
            model = get_model_by_item_type(rule_instance.category)
            item_instance = model.objects.get(id=rule_instance.item_id)
            item_name = item_instance.name
            item_price = item_instance.price
            send_browse_notify_notify_email_with_fatigue_control(item_name, item_price, user_instance)
        except ObjectDoesNotExist:
            # 如果没有找到对应的条目，处理异常
            logger.info(f"No Rule found with id {rule_id}")
            return

        logger.info(f"browse notify  handled, message: {body}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


def send_browse_notify_notify_email_with_fatigue_control(item_name, item_price, user_instance):
    user_id = user_instance.id
    redis_user_key = user_redis_pre + str(user_id)
    fatigue_value = redis_client.get(redis_user_key)
    if fatigue_value is not None:
        # Convert fatigue_value from bytes to int before comparison
        fatigue_value = int(fatigue_value)
        if fatigue_value >= 3:
            logger.info(f"send email too much, userId: {user_id}")
            return
    subject = "CONCORDIA TRAVEL:The product awaits your purchase"
    # send email notification
    message = ("The product " + item_name + " you've been eyeing is now priced at $ " + str(item_price) +
               "! We're eagerly awaiting your purchase!")
    send_custom_email(subject, message, [user_instance.email])
    redis_client.incr(redis_user_key)
    set_expiry_at_midnight(redis_user_key)


def set_expiry_at_midnight(redis_key):
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    seconds_until_midnight = (midnight - now).seconds

    redis_client.expire(redis_key, seconds_until_midnight)
