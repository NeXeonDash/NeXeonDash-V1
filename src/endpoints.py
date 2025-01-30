import bcrypt
import os
import json
from flask import render_template, request, redirect, session, url_for, flash
from werkzeug.utils import secure_filename
import uuid

from .api import (
    create_pterodactyl_user,
    update_pterodactyl_user_info,
    delete_pterodactyl_user,
    create_pterodactyl_server,
    delete_pterodactyl_server
)
from .middleware.auth import login_required
from .database import (
    db,  # Import the database connection if needed
    get_user_by_username,
    get_user_by_email,
    insert_user,
    update_user,
    delete_user_by_username,
    get_user_by_id,
    insert_server,
    get_servers_by_user_id,
    get_server_count_by_user_id,
    get_total_resource_usage_by_user_id,
    delete_server_by_id,
    get_server_by_id
)

def register_endpoints(app):
    # IMPORTANT: Set a secret key so that sessions work properly.
    # Without this, Flask will not maintain client sessions consistently.
    # If you already have a secret key in your main application code, remove or modify this as needed.
    app.secret_key = os.getenv('SECRET_KEY', 'NeXeonDash')

    # Load admin account details
    admin_account_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'admin_account.json'
    )
    with open(admin_account_path, 'r') as f:
        admin_data = json.load(f)

    ADMIN_USERNAME = admin_data.get('admin_username', 'admin')
    ADMIN_PASSWORD = admin_data.get('admin_password', 'admin123')

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/success')
    def success_page():
        return render_template('success.html')

    @app.route('/failure')
    def failure_page():
        return render_template('failure.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            try:
                username = request.form.get('username')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                email = request.form.get('email')

                if not all([username, password, confirm_password, email]):
                    return redirect('/failure')

                if password != confirm_password or len(password) < 8:
                    return redirect('/failure')

                # Check for existing user
                if get_user_by_username(username):
                    return redirect('/failure')
                if get_user_by_email(email):
                    return redirect('/failure')

                # Create in Pterodactyl
                ptero_user = create_pterodactyl_user(username, email, password)
                if not ptero_user:
                    return redirect('/failure')

                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                insert_user(username, email, hashed, ptero_user['attributes']['id'])

                return redirect('/success')
            except Exception as e:
                print("Registration error:", e)
                return redirect('/failure')
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = get_user_by_username(username)
            print("DEBUG: login user fetch =>", user)

            if not user:
                return redirect('/failure')

            stored_hash = user['password']
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                session['username'] = username
                return redirect('/dashboard')
            else:
                return redirect('/failure')
        return render_template('login.html')

    @app.route('/settings')
    @login_required
    def settings():
        user = get_user_by_username(session['username'])
        print("DEBUG: settings user =>", dict(user) if user else None)
        return render_template(
            'settings.html',
            username=user['username'] if user else '',
            profile_picture=user['profile_picture'] if user else None,
            ptero_domain=os.getenv('PTERO_DOMAIN'),
            email=user['email'] if user else ''
        )

    @app.route('/update_settings', methods=['POST'])
    @login_required
    def update_settings():
        try:
            current_user = get_user_by_username(session['username'])
            if not current_user:
                return redirect('/failure')

            new_username = request.form.get('username', current_user['username'])
            new_email = request.form.get('email', current_user['email'])
            new_password = request.form.get('password') or None
            confirm_password = request.form.get('confirm_password') or None
            profile_picture = request.files.get('profile_picture')

            print("DEBUG: update_settings =>", new_username, new_email, new_password)

            if new_password and confirm_password:
                if new_password != confirm_password or len(new_password) < 8:
                    return redirect('/failure')
            else:
                new_password = None

            if new_username != current_user['username']:
                if get_user_by_username(new_username):
                    return redirect('/failure')

            ptero_update = update_pterodactyl_user_info(
                user_id=current_user['ptero_id'],
                new_username=new_username,
                new_email=new_email,
                new_password=new_password
            )
            if not ptero_update:
                return redirect('/failure')

            updates = {}

            if new_username != current_user['username']:
                updates['username'] = new_username
                session['username'] = new_username

            if new_email != current_user['email']:
                updates['email'] = new_email

            if new_password:
                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                updates['password'] = hashed

            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
            uploads_dir = os.path.join(static_dir, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)

            if profile_picture and profile_picture.filename != '':
                secure_name = secure_filename(profile_picture.filename)
                unique_name = f"{uuid.uuid4()}_{secure_name}"
                filepath = os.path.join(uploads_dir, unique_name)
                profile_picture.save(filepath)

                picture_url = url_for('static', filename=f'uploads/{unique_name}', _external=False)
                updates['profile_picture'] = picture_url

            if updates:
                update_user(current_user['username'], updates)

            return redirect('/success')
        except Exception as e:
            print("Settings update error:", e)
            return redirect('/failure')

    @app.route('/delete_account', methods=['POST'])
    @login_required
    def delete_account():
        try:
            current_user = get_user_by_username(session['username'])
            if not current_user:
                return redirect('/failure')

            # Delete from Pterodactyl
            if not delete_pterodactyl_user(current_user['ptero_id']):
                return redirect('/failure')

            delete_user_by_username(session['username'])

            session.pop('username', None)
            return redirect('/success')
        except Exception as e:
            print("Account deletion error:", e)
            return redirect('/failure')

    @app.route('/servers')
    @login_required
    def servers():
        user = get_user_by_username(session['username'])
        if not user:
            return redirect('/failure')
            
        servers = get_servers_by_user_id(user['id'])
        return render_template(
            'servers.html',
            username=user['username'],
            profile_picture=user['profile_picture'],
            ptero_domain=os.getenv('PTERO_DOMAIN'),
            servers=servers
        )

    @app.route('/delete_server/<int:server_id>', methods=['POST'])
    @login_required
    def delete_server(server_id):
        try:
            user = get_user_by_username(session['username'])
            if not user:
                return redirect('/failure')

            server = get_server_by_id(server_id)
            print("DEBUG: Deleting server =>", dict(server) if server else None)
            
            if not server or server['user_id'] != user['id']:
                print("DEBUG: Server not found or unauthorized")
                return redirect('/failure')

            # Delete from Pterodactyl first
            print("DEBUG: Attempting to delete from Pterodactyl with ID:", server['ptero_server_id'])
            if not delete_pterodactyl_server(server['ptero_server_id']):
                print("DEBUG: Failed to delete from Pterodactyl")
                return redirect('/failure')

            # Then delete from local database
            delete_server_by_id(server_id)

            return redirect('/servers')
        except Exception as e:
            print("Server deletion error:", e)
            return redirect('/failure')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = get_user_by_username(session['username'])
        print("DEBUG: dashboard user =>", dict(user) if user else None)
        return render_template(
            'dashboard.html',
            username=user['username'] if user else '',
            profile_picture=user['profile_picture'] if user else None,
            ptero_domain=os.getenv('PTERO_DOMAIN')
        )

    @app.route('/create_server', methods=['GET', 'POST'])
    @login_required
    def create_server_route():
        with open('user_limits.json', 'r') as f:
            user_limits = json.load(f)
        max_servers_per_user = user_limits.get('max_servers_per_user', 1)

        with open('server_limits.json', 'r') as f:
            server_limits = json.load(f)
        default_values = server_limits.get('default_values', {})
        max_memory_per_user = default_values.get('memory', 1024)  # in MB
        max_cpu_per_user = default_values.get('cpu', 100)  # in %
        max_disk_per_user = default_values.get('disk', 10240)  # in MB
        max_backups_per_user = default_values.get('backups', 0)
        max_databases_per_user = default_values.get('databases', 0)

        current_user = get_user_by_username(session['username'])
        if not current_user:
            return redirect('/failure')

        user_id = current_user['id']
        servers = get_servers_by_user_id(user_id)
        existing_count = get_server_count_by_user_id(user_id)

        # Calculate current resource usage
        total_memory_used = sum(server['memory'] for server in servers)
        total_cpu_used = sum(server['cpu'] for server in servers)
        total_disk_used = sum(server['disk'] if 'disk' in server.keys() else 0 for server in servers)
        total_backups_used = sum(server['backups'] if 'backups' in server.keys() else 0 for server in servers)
        total_databases_used = sum(server['databases'] if 'databases' in server.keys() else 0 for server in servers)

        if request.method == 'GET':
            if existing_count >= max_servers_per_user:
                return redirect('/failure')

            return render_template(
                'create_server.html',
                username=current_user['username'],
                profile_picture=current_user['profile_picture'],
                default_values=default_values,
                existing_count=existing_count,
                max_servers_per_user=max_servers_per_user,
                total_memory_used=total_memory_used,
                total_cpu_used=total_cpu_used,
                total_disk_used=total_disk_used,
                total_backups_used=total_backups_used,
                total_databases_used=total_databases_used,
                max_memory_per_user=max_memory_per_user,
                max_cpu_per_user=max_cpu_per_user,
                max_disk_per_user=max_disk_per_user,
                max_backups_per_user=max_backups_per_user,
                max_databases_per_user=max_databases_per_user
            )

        try:
            if existing_count >= max_servers_per_user:
                return redirect('/failure')

            server_name = request.form.get('server_name')
            egg_id = request.form.get('egg_id')
            build_number = request.form.get('build_number')
            memory = int(request.form.get('memory', default_values.get('memory', 1024)))
            cpu = int(request.form.get('cpu', default_values.get('cpu', 100)))
            disk = int(request.form.get('disk', default_values.get('disk', 10240)))
            backups = int(request.form.get('backups', default_values.get('backups', 0)))
            databases = int(request.form.get('databases', default_values.get('databases', 0)))

            # Ensure we have all fields including build_number
            if not all([server_name, egg_id, build_number]):
                return redirect('/failure')

            # Check if user has enough resources
            if (total_memory_used + memory) > max_memory_per_user or \
               (total_cpu_used + cpu) > max_cpu_per_user or \
               (total_disk_used + disk) > max_disk_per_user or \
               (total_backups_used + backups) > max_backups_per_user or \
               (total_databases_used + databases) > max_databases_per_user:
                return redirect('/failure')

            owner_id = current_user['ptero_id']
            # Pass build_number as the version
            server_response = create_pterodactyl_server(
                owner_id=owner_id,
                server_name=server_name,
                egg_id=egg_id,
                memory=memory,
                cpu=cpu,
                disk=disk,
                backups=backups,
                databases=databases,
                version=build_number
            )
            if not server_response:
                return redirect('/failure')

            ptero_sid = server_response['attributes']['id']
            # Update insert_server to include disk, backups, databases
            insert_server(user_id, ptero_sid, server_name, memory, cpu, disk, backups, databases)

            return redirect('/success')
        except Exception as e:
            print("Server creation error:", e)
            return redirect('/failure')

    # ADMIN SECTION

    @app.route('/admin_login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'GET':
            return render_template('admin_login.html')

        admin_username = request.form.get('admin_username')
        admin_password = request.form.get('admin_password')

        if admin_username == ADMIN_USERNAME and admin_password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect('/admin_dashboard')
        else:
            return redirect('/failure')

    @app.route('/admin_logout')
    def admin_logout():
        session.pop('is_admin', None)
        return redirect('/admin_login')

    @app.route('/admin_dashboard')
    def admin_dashboard():
        if not session.get('is_admin'):
            return redirect('/failure')

        # Fetch all users for the admin dashboard
        cursor = db.execute("SELECT id, username, email, ptero_id FROM users")
        all_users = cursor.fetchall()
        print("DEBUG: admin_dashboard all_users =>", [dict(u) for u in all_users])
        return render_template('admin_dashboard.html', users=all_users)

    @app.route('/admin_delete_user', methods=['POST'])
    def admin_delete_user():
        if not session.get('is_admin'):
            return redirect('/failure')
        user_id = request.form.get('user_id')
        if not user_id:
            return redirect('/failure')

        user = get_user_by_id(user_id)
        if user and user["ptero_id"] is not None:
            if not delete_pterodactyl_user(user["ptero_id"]):
                return redirect('/failure')

        delete_user_by_username(user['username'])
        return redirect('/admin_dashboard')
