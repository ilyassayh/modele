from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import login_required
import google.generativeai as genai

chat_bp = Blueprint('chat', __name__)

gemini_model = genai.GenerativeModel("gemini-1.5-flash")

@chat_bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if 'chat_history' not in session:
        session['chat_history'] = [
            {'sender': 'support', 'message': 'Hello! How can I help you with your car repair or estimate today?'}
        ]
    chat_history = session['chat_history']
    if request.method == 'POST':
        user_msg = request.form.get('message', '').strip()
        if user_msg:
            chat_history.append({'sender': 'user', 'message': user_msg})
            # Compose prompt for Gemini
            prompt = "You are a helpful car repair assistant. Respond conversationally to the user's question."
            conversation = "\n".join([
                ("User: " + m['message']) if m['sender'] == 'user' else ("Support: " + m['message'])
                for m in chat_history
            ])
            try:
                response = gemini_model.generate_content([
                    prompt + "\n" + conversation
                ])
                reply = response.text.strip()
            except Exception as e:
                reply = "Sorry, I'm having trouble connecting to the AI right now."
            chat_history.append({'sender': 'support', 'message': reply})
            session['chat_history'] = chat_history
        return redirect(url_for('chat.chat'))
    return render_template('chat/chat.html', chat_history=chat_history)

@chat_bp.route('/chat/new')
@login_required
def new_chat():
    session.pop('chat_history', None)
    return redirect(url_for('chat.chat')) 