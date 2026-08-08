from app import create_app
from app.models.user import User
app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()
with app.app_context():
    user = User.get_by_id('bdd48bd9-cdff-48a6-a67a-880ea541b67d')
    with client.session_transaction() as sess:
        sess['_user_id'] = user.id
        sess['_fresh'] = True
    resp = client.get('/orders/ORD-20260801-4365F6')
    print('Status:', resp.status_code)
    if resp.status_code != 200:
        print('Error:', resp.get_data(as_text=True))
