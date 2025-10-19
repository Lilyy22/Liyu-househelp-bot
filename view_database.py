import sqlite3
from tabulate import tabulate
from datetime import datetime

DATABASE_FILE = 'liyu_agency.db'

def view_users_table():
    """Display all users in a formatted table."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, telegram_id, username, first_name, last_name, created_at FROM users')
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            print("\n❌ No users found in database.\n")
            return
        
        print("\n" + "="*120)
        print("👥 USERS TABLE")
        print("="*120)
        
        headers = ["User ID", "Telegram ID", "Username", "First Name", "Last Name", "Created At"]
        print(tabulate(users, headers=headers, tablefmt="grid"))
        print(f"\n✅ Total Users: {len(users)}\n")
        
    except Exception as e:
        print(f"❌ Error reading users table: {e}")

def view_service_requests_table():
    """Display all service requests in a formatted table."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT request_id, user_id, name, phone, location, service_type, services, submitted_at 
            FROM service_requests
            ORDER BY submitted_at DESC
        ''')
        requests = cursor.fetchall()
        conn.close()
        
        if not requests:
            print("\n❌ No service requests found in database.\n")
            return
        
        print("\n" + "="*180)
        print("📋 SERVICE REQUESTS TABLE")
        print("="*180)
        
        headers = ["Request ID", "User ID", "Name", "Phone", "Location", "Service Type", "Services", "Submitted At"]
        print(tabulate(requests, headers=headers, tablefmt="grid"))
        print(f"\n✅ Total Requests: {len(requests)}\n")
        
    except Exception as e:
        print(f"❌ Error reading service requests table: {e}")

def view_detailed_requests():
    """Display service requests with more readable formatting."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT request_id, name, phone, location, service_type, services, submitted_at 
            FROM service_requests
            ORDER BY submitted_at DESC
        ''')
        requests = cursor.fetchall()
        conn.close()
        
        if not requests:
            print("\n❌ No service requests found in database.\n")
            return
        
        print("\n" + "="*100)
        print("📝 DETAILED SERVICE REQUESTS")
        print("="*100)
        
        for idx, request in enumerate(requests, 1):
            request_id, name, phone, location, service_type, services, submitted_at = request
            print(f"\n📌 Request #{request_id}")
            print(f"   👤 Name: {name}")
            print(f"   📞 Phone: {phone}")
            print(f"   📍 Location: {location}")
            print(f"   ⚡ Service Type: {service_type}")
            print(f"   🛠️  Services: {services}")
            print(f"   📅 Submitted: {submitted_at}")
            print("-" * 100)
        
        print(f"\n✅ Total Requests: {len(requests)}\n")
        
    except Exception as e:
        print(f"❌ Error reading detailed requests: {e}")

def get_database_stats():
    """Display database statistics."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Count users
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        # Count service requests
        cursor.execute('SELECT COUNT(*) FROM service_requests')
        request_count = cursor.fetchone()[0]
        
        # Get latest request
        cursor.execute('SELECT submitted_at FROM service_requests ORDER BY submitted_at DESC LIMIT 1')
        latest_request = cursor.fetchone()
        
        conn.close()
        
        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        print(f"👥 Total Users: {user_count}")
        print(f"📋 Total Service Requests: {request_count}")
        if latest_request:
            print(f"⏰ Latest Request: {latest_request[0]}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

def export_to_csv():
    """Export database to CSV files."""
    try:
        import csv
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Export users
        cursor.execute('SELECT user_id, telegram_id, username, first_name, last_name, created_at FROM users')
        users = cursor.fetchall()
        
        if users:
            with open('users_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['User ID', 'Telegram ID', 'Username', 'First Name', 'Last Name', 'Created At'])
                writer.writerows(users)
            print("✅ Users exported to users_export.csv")
        
        # Export service requests
        cursor.execute('''
            SELECT request_id, user_id, name, phone, location, service_type, services, submitted_at 
            FROM service_requests
        ''')
        requests = cursor.fetchall()
        
        if requests:
            with open('service_requests_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Request ID', 'User ID', 'Name', 'Phone', 'Location', 'Service Type', 'Services', 'Submitted At'])
                writer.writerows(requests)
            print("✅ Service requests exported to service_requests_export.csv")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")

def main():
    """Main menu for database viewer."""
    print("\n" + "="*60)
    print("🗄️  LIYU AGENCY - DATABASE VIEWER")
    print("="*60)
    
    while True:
        print("\n📊 Choose an option:")
        print("1. View Users Table")
        print("2. View Service Requests Table")
        print("3. View Detailed Service Requests")
        print("4. View Database Statistics")
        print("5. Export to CSV")
        print("6. View All (Users + Requests + Stats)")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            view_users_table()
        elif choice == '2':
            view_service_requests_table()
        elif choice == '3':
            view_detailed_requests()
        elif choice == '4':
            get_database_stats()
        elif choice == '5':
            export_to_csv()
        elif choice == '6':
            get_database_stats()
            view_users_table()
            view_service_requests_table()
        elif choice == '7':
            print("\n👋 Goodbye!\n")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
