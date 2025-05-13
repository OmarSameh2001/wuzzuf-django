import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

rabbitmq_url = os.getenv("RABBITMQ_URL")

def send_to_queue(queue_name: str, request_type: str, endpoint: str, body: dict = {}) -> bool:
    """
    Send a message to a specific RabbitMQ queue.

    :param queue_name: Name of the queue to publish to.
    :param body: Dictionary payload to send.
    :param rabbitmq_url: CloudAMQP URL (default is placeholder).
    :param type: post,put,patch,...
    :param endpoint: ats/, jobs/, analysis/
    """
    try:
        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        channel = connection.channel()

        # Declare the queue to make sure it exists
        channel.queue_declare(queue=queue_name, durable=True)
        body["endpoint"] = endpoint
        body["type"] = request_type
        # Publish the message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )
        connection.close()
        return True
    except Exception as e:
        # Log this in production!
        print(f"[RabbitMQ Error] {e}")
        return False