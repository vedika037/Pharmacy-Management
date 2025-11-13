from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ------------------ DATABASE CONNECTION ------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # update if needed
        database="pharmacy_management"
    )


# ------------------ DASHBOARD ------------------
@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total_medicines FROM medicine")
    total_medicines = cur.fetchone()['total_medicines']

    cur.execute("SELECT COUNT(*) AS total_customers FROM customer")
    total_customers = cur.fetchone()['total_customers']

    cur.execute("SELECT COUNT(*) AS total_suppliers FROM supplier")
    total_suppliers = cur.fetchone()['total_suppliers']

    cur.execute("SELECT COUNT(*) AS total_orders FROM orders")
    total_orders = cur.fetchone()['total_orders'] or 0

    conn.close()

    return render_template(
        "index.html",
        total_medicines=total_medicines,
        total_customers=total_customers,
        total_suppliers=total_suppliers,
        total_orders=total_orders,
    )


# ------------------ CUSTOMERS (CRUD + AUDIT) ------------------
@app.route('/customers')
def customers():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM customer ORDER BY cid ASC")
    customers = cur.fetchall()

    cur.execute("SELECT * FROM customer_audit ORDER BY action_time DESC")
    audit = cur.fetchall()
    conn.close()
    return render_template('customer.html', customers=customers, audit=audit)


@app.route('/add_customer', methods=['POST'])
def add_customer():
    cname = request.form['cname']
    caddress = request.form['caddress']
    cphone = request.form['cphone']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # ✅ Generate next cid manually
    cur.execute("SELECT IFNULL(MAX(cid), 0) + 1 AS next_id FROM customer")
    next_cid = cur.fetchone()['next_id']

    cur.execute("""
        INSERT INTO customer (cid, cname, caddress, cphone)
        VALUES (%s, %s, %s, %s)
    """, (next_cid, cname, caddress, cphone))
    conn.commit()

    # Audit log
    cur.execute("""
        INSERT INTO customer_audit (customer_id, customer_name, action_time, action)
        VALUES (%s, %s, NOW(), 'Added')
    """, (next_cid, cname))
    conn.commit()

    conn.close()
    flash("✅ Customer Added Successfully!", "success")
    return redirect(url_for('customers'))



@app.route('/update_customer/<int:cid>', methods=['POST'])
def update_customer(cid):
    cname = request.form['cname']
    caddress = request.form['caddress']
    cphone = request.form['cphone']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE customer 
        SET cname=%s, caddress=%s, cphone=%s 
        WHERE cid=%s
    """, (cname, caddress, cphone, cid))
    conn.commit()

    # Log update
    cur.execute("""
        INSERT INTO customer_audit (customer_id, customer_name, action_time, action)
        VALUES (%s, %s, NOW(), 'Updated')
    """, (cid, cname))
    conn.commit()

    conn.close()
    flash("✏️ Customer Updated Successfully!", "info")
    return redirect(url_for('customers'))


@app.route('/delete_customer/<int:cid>')
def delete_customer(cid):
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch name for audit
    cur.execute("SELECT cname FROM customer WHERE cid=%s", (cid,))
    result = cur.fetchone()
    cname = result[0] if result else "Unknown"

    cur.execute("DELETE FROM customer WHERE cid=%s", (cid,))
    conn.commit()

    cur.execute("""
        INSERT INTO customer_audit (customer_id, customer_name, action_time, action)
        VALUES (%s, %s, NOW(), 'Deleted')
    """, (cid, cname))
    conn.commit()

    conn.close()
    flash("🗑️ Customer Deleted Successfully!", "danger")
    return redirect(url_for('customers'))
# ------------------ MEDICINES (CRUD) ------------------
@app.route('/medicines')
def medicines():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM medicine ORDER BY mid ASC")
    medicines = cur.fetchall()
    conn.close()
    return render_template('medicine.html', medicines=medicines)


@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    mname = request.form['mname']
    category = request.form['category']
    price = request.form['price']
    stock = request.form.get('stock')
    expiry_date = request.form.get('expiry_date')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO medicine (mname, category, price, stock, expiry_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (mname, category, price, stock, expiry_date))
    conn.commit()
    conn.close()
    flash(f"💊 Medicine '{mname}' added successfully!", "success")
    return redirect(url_for('medicines'))



@app.route('/update_medicine/<int:mid>', methods=['POST'])
def update_medicine(mid):
    mname = request.form['mname']
    category = request.form['category']
    price = request.form['price']
    stock = request.form['stock']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE medicine SET mname=%s, category=%s, price=%s, stock=%s WHERE mid=%s",
                (mname, category, price, stock, mid))
    conn.commit()
    conn.close()
    flash("✏️ Medicine updated successfully!", "info")
    return redirect(url_for('medicines'))


@app.route('/delete_medicine/<int:mid>')
def delete_medicine(mid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM medicine WHERE mid=%s", (mid,))
    conn.commit()
    conn.close()
    flash("🗑️ Medicine deleted successfully!", "danger")
    return redirect(url_for('medicines'))


# ------------------ SUPPLIERS (CRUD) ------------------
@app.route('/supplier')
def supplier():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM supplier ORDER BY sid ASC")
    suppliers = cur.fetchall()
    conn.close()
    return render_template('supplier.html', suppliers=suppliers)


@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    try:
        sname = request.form['sname']
        saddress = request.form['saddress']
        sphone = request.form['sphone']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # ✅ Generate next sid manually
        cur.execute("SELECT IFNULL(MAX(sid), 0) + 1 AS next_id FROM supplier")
        next_sid = cur.fetchone()['next_id']

        # ✅ Insert supplier with generated sid
        cur.execute("""
            INSERT INTO supplier (sid, sname, saddress, sphone)
            VALUES (%s, %s, %s, %s)
        """, (next_sid, sname, saddress, sphone))

        conn.commit()
        flash("✅ Supplier added successfully!", "success")

    except Exception as e:
        flash(f"❌ Error adding supplier: {e}", "danger")

    finally:
        cur.close()
        conn.close()

    return redirect(url_for('supplier'))



@app.route('/update_supplier/<int:sid>', methods=['POST'])
def update_supplier(sid):
    sname = request.form['sname']
    saddress = request.form['saddress']
    sphone = request.form['sphone']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE supplier
        SET sname=%s, saddress=%s, sphone=%s
        WHERE sid=%s
    """, (sname, saddress, sphone, sid))
    conn.commit()
    conn.close()
    flash("✏️ Supplier updated successfully!", "info")
    return redirect(url_for('supplier'))


@app.route('/delete_supplier/<int:sid>')
def delete_supplier(sid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM supplier WHERE sid=%s", (sid,))
    conn.commit()
    conn.close()
    flash("🗑️ Supplier deleted successfully!", "danger")
    return redirect(url_for('supplier'))

# ------------------ ORDERS (CRUD) ------------------
@app.route('/orders')
def orders():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM orders ORDER BY order_date DESC")
    orders = cur.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)


@app.route('/add_order', methods=['POST'])
def add_order():
    try:
        invoice = request.form['invoice']
        order_date = request.form['order_date']
        gst = request.form['gst']
        total_amount = request.form['total_amount']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # ✅ Generate next order ID manually
        cur.execute("SELECT IFNULL(MAX(oid), 0) + 1 AS next_id FROM orders")
        next_oid = cur.fetchone()['next_id']

        # ✅ Insert with generated OID
        cur.execute("""
            INSERT INTO orders (oid, invoice, order_date, gst, total_amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (next_oid, invoice, order_date, gst, total_amount))

        conn.commit()
        conn.close()
        flash("🧾 Order Added Successfully!", "success")
    except Exception as e:
        flash(f"⚠️ Error adding order: {e}", "danger")
    return redirect(url_for('orders'))



@app.route('/update_order/<int:oid>', methods=['POST'])
def update_order(oid):
    try:
        invoice = request.form['invoice']
        order_date = request.form['order_date']
        gst = request.form['gst']
        total_amount = request.form['total_amount']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE orders
            SET invoice=%s, order_date=%s, gst=%s, total_amount=%s
            WHERE oid=%s
        """, (invoice, order_date, gst, total_amount, oid))
        conn.commit()
        conn.close()
        flash("✏️ Order Updated Successfully!", "info")
    except Exception as e:
        flash(f"⚠️ Error updating order: {e}", "danger")
    return redirect(url_for('orders'))


@app.route('/delete_order/<int:oid>')
def delete_order(oid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE oid=%s", (oid,))
        conn.commit()
        conn.close()
        flash("🗑️ Order Deleted Successfully!", "info")
    except Exception as e:
        flash(f"⚠️ Error deleting order: {e}", "danger")
    return redirect(url_for('orders'))


# ---------------- PURCHASES ----------------
@app.route('/purchase')
def purchase():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch purchase details with supplier and medicine info (joined for readability)
    cur.execute("""
        SELECT p.pid, s.sname AS supplier_name, m.mname AS medicine_name, 
               p.purchase_date, p.quantity, p.cost_per_unit
        FROM purchases p
        JOIN supplier s ON p.sid = s.sid
        JOIN medicine m ON p.mid = m.mid
        ORDER BY p.purchase_date DESC
    """)
    purchases = cur.fetchall()

    # For dropdowns in form
    cur.execute("SELECT sid, sname FROM supplier")
    suppliers = cur.fetchall()
    cur.execute("SELECT mid, mname FROM medicine")
    medicines = cur.fetchall()

    conn.close()
    return render_template('purchase.html', purchases=purchases, suppliers=suppliers, medicines=medicines)


@app.route('/add_purchase', methods=['POST'])
def add_purchase():
    try:
        sid = request.form['sid']
        mid = request.form['mid']
        purchase_date = request.form['purchase_date']
        quantity = request.form['quantity']
        cost_per_unit = request.form['cost_per_unit']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # ✅ Generate next purchase ID manually
        cur.execute("SELECT IFNULL(MAX(pid), 0) + 1 AS next_id FROM purchases")
        next_pid = cur.fetchone()['next_id']

        cur.execute("""
            INSERT INTO purchases (pid, sid, mid, purchase_date, quantity, cost_per_unit)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (next_pid, sid, mid, purchase_date, quantity, cost_per_unit))

        conn.commit()
        conn.close()
        flash("✅ Purchase Added Successfully!", "success")

    except Exception as e:
        flash(f"⚠️ Error adding purchase: {e}", "danger")

    # ✅ Correct redirect (same as route function)
    return redirect(url_for('purchase'))


@app.route('/delete_purchase/<int:pid>')
def delete_purchase(pid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM purchases WHERE pid = %s", (pid,))
        conn.commit()
        conn.close()
        flash("🗑️ Purchase Deleted Successfully!", "info")
    except Exception as e:
        flash(f"⚠️ Error deleting purchase: {e}", "danger")

    return redirect(url_for('purchase'))



# ---------------- DELIVERIES ----------------
@app.route('/deliveries')
def deliveries():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # ✅ Only join with deliveryperson
    cur.execute("""
        SELECT d.delivery_id, dp.did, dp.dname AS delivery_person,
               d.delivery_date, d.status, d.remarks
        FROM deliveries d
        JOIN deliveryperson dp ON d.did = dp.did
        ORDER BY d.delivery_date DESC
    """)
    deliveries = cur.fetchall()

    # Fetch delivery persons for dropdown
    cur.execute("SELECT did, dname FROM deliveryperson")
    deliverypersons = cur.fetchall()

    conn.close()
    return render_template('deliveries.html',
                           deliveries=deliveries,
                           deliverypersons=deliverypersons)


@app.route('/add_delivery', methods=['POST'])
def add_delivery():
    did = request.form['did']
    delivery_date = request.form['delivery_date']
    status = request.form['status']
    remarks = request.form['remarks']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO deliveries (did, delivery_date, status, remarks)
        VALUES (%s, %s, %s, %s)
    """, (did, delivery_date, status, remarks))
    conn.commit()
    conn.close()
    flash("🚚 Delivery Record Added Successfully!", "success")
    return redirect(url_for('deliveries'))



@app.route('/delete_delivery/<int:delivery_id>')
def delete_delivery(delivery_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM deliveries WHERE delivery_id=%s", (delivery_id,))
    conn.commit()
    conn.close()
    flash("🗑️ Delivery Deleted Successfully!", "info")
    return redirect(url_for('deliveries'))


# ---------------- DELIVERY PERSON ----------------
@app.route('/deliveryperson')
def deliveryperson():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM deliveryperson ORDER BY did ASC")
    data = cur.fetchall()
    conn.close()
    return render_template('deliveryperson.html', data=data)


@app.route('/add_deliveryperson', methods=['POST'])
def add_deliveryperson():
    try:
        dname = request.form['dname']
        daddress = request.form['daddress']
        dphone = request.form['dphone']
        registration = request.form['registration']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # ✅ Generate next delivery person ID manually
        cur.execute("SELECT IFNULL(MAX(did), 0) + 1 AS next_id FROM deliveryperson")
        next_did = cur.fetchone()['next_id']

        cur.execute("""
            INSERT INTO deliveryperson (did, dname, daddress, dphone, registration)
            VALUES (%s, %s, %s, %s, %s)
        """, (next_did, dname, daddress, dphone, registration))

        conn.commit()
        conn.close()
        flash("🚴 Delivery Person Added Successfully!", "success")

    except Exception as e:
        flash(f"⚠️ Error adding delivery person: {e}", "danger")

    return redirect('/deliveryperson')



@app.route('/delete_deliveryperson/<int:did>')
def delete_deliveryperson(did):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM deliveryperson WHERE did=%s", (did,))
        conn.commit()
        conn.close()
        flash("🗑️ Delivery Person Deleted Successfully!", "info")
    except Exception as e:
        flash(f"⚠️ Error deleting delivery person: {e}", "danger")
    return redirect('/deliveryperson')


@app.route('/update_deliveryperson/<int:did>', methods=['POST'])
def update_deliveryperson(did):
    try:
        dname = request.form['dname']
        daddress = request.form['daddress']
        dphone = request.form['dphone']
        registration = request.form['registration']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE deliveryperson
            SET dname=%s, daddress=%s, dphone=%s, registration=%s
            WHERE did=%s
        """, (dname, daddress, dphone, registration, did))
        conn.commit()
        conn.close()
        flash("✅ Delivery Person Updated Successfully!", "success")
    except Exception as e:
        flash(f"⚠️ Error updating delivery person: {e}", "danger")
    return redirect('/deliveryperson')



@app.route('/customerorderdetails')
def customerorderdetails():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            cod.cod_id,
            c.cname AS customer_name,
            o.invoice AS invoice_no,
            m.mname AS medicine_name,
            cod.quantity,
            cod.price_per_unit,
            cod.discount,
            cod.payment_mode,
            cod.order_status
        FROM customerorderdetails cod
        LEFT JOIN customer c ON cod.cid = c.cid
        LEFT JOIN orders o ON cod.oid = o.oid
        LEFT JOIN medicine m ON cod.mid = m.mid
        ORDER BY cod.cod_id DESC
    """)
    data = cur.fetchall()
    conn.close()
    return render_template('customerorderdetails.html', data=data)




# ------------------ LOW STOCK ALERT ------------------
@app.route('/lowstock')
def lowstock():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT mid, mname, category, price, 
               IFNULL(stock, 0) AS stock
        FROM medicine
        WHERE IFNULL(stock, 0) < 50
        ORDER BY stock ASC
    """)
    data = cur.fetchall()
    conn.close()
    return render_template('lowstock.html', data=data)


# ------------------ EXPIRY ALERT ------------------
@app.route('/expiry_alert')
def expiry_alert():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT mid, mname, category, price, expiry_date
        FROM medicine
        WHERE expiry_date IS NOT NULL 
          AND expiry_date <= (CURDATE() + INTERVAL 60 DAY)
        ORDER BY expiry_date ASC
    """)
    data = cur.fetchall()
    conn.close()
    return render_template('expiry_alert.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
