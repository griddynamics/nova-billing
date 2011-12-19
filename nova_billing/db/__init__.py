def get_api():
    from nova_billing.db.sqlalchemy import api
    return api

api = get_api()
