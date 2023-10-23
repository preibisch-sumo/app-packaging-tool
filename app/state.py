
class State:
    def __init__(self):
        self.deployment = None
        self.acc_name = None
        self.access_key = None
        self.access_id = None
        self.app_work_name = None

    def __str__(self):
        return (f"State(deployment={self.deployment}, acc_name={self.acc_name}, "
                f"access_key={self.access_key}, access_id={self.access_id}, app_work_name={self.app_work_name})")

    def log_in(self, name, deployment, access_key, access_id):
        self.deployment = deployment
        self.acc_name = name
        self.access_key = access_key
        self.access_id = access_id
