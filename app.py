import os,io,uuid
from functools import wraps
from flask import Flask,request,redirect,url_for,session,flash,render_template_string,send_file
from werkzeug.security import generate_password_hash,check_password_hash
import mysql.connector,pandas as pd,matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
app=Flask(__name__);app.secret_key=os.getenv("SECRET_KEY","change-this-secret")
DB=dict(host=os.getenv("DB_HOST","127.0.0.1"),user=os.getenv("DB_USER","root"),password=os.getenv("DB_PASSWORD",""),database=os.getenv("DB_NAME","shopsphere_db"),port=int(os.getenv("DB_PORT","3306")))
def q(sql,args=(),one=False,commit=False):
 c=mysql.connector.connect(**DB);k=c.cursor(dictionary=True)
 try:
  k.execute(sql,args);r=k.fetchone() if one else k.fetchall()
  if commit:c.commit()
  return r
 finally:k.close();c.close()
def login(f):
 @wraps(f)
 def w(*a,**kw):
  if not session.get("uid"):return redirect(url_for("signin"))
  return f(*a,**kw)
 return w
def admin(f):
 @wraps(f)
 def w(*a,**kw):
  if session.get("role")!="admin":return redirect(url_for("signin"))
  return f(*a,**kw)
 return w
BASE="""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{{ title }} · ShopSphere</title><link href='https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Manrope:wght@700;800&display=swap' rel=stylesheet><link rel=stylesheet href=/static/style.css></head><body><header><a class=logo href=/>◈ ShopSphere<span>.</span></a><nav><a href=/products>Discover</a>{% if session.get('uid') %}<a href=/account>My orders</a>{% if session.get('role')=='admin' %}<a href=/admin>Admin</a>{% endif %}<a href=/logout>Log out</a>{% else %}<a href=/login>Sign in</a><a href=/register>Join</a>{% endif %}<a href=/cart>Bag ({{ bag }})</a></nav></header>{% for cat,msg in get_flashed_messages(with_categories=true) %}<div class='flash {{cat}}'>{{msg}}</div>{% endfor %}<main>{{ body|safe }}</main><footer>ShopSphere · Thoughtful finds. Better everyday.<small>Educational demonstration · No real payments processed</small></footer></body></html>"""
def page(body,title="ShopSphere",**ctx):
 return render_template_string(BASE,body=render_template_string(body,**ctx),title=title,bag=sum(x["qty"] for x in session.get("cart",{}).values()))
CARD="""<div class=grid>{% for p in products %}<article class=card><a href='/product/{{p.product_id}}'><img src='{{p.image_url or "https://placehold.co/600x600?text=ShopSphere"}}' onerror=\"this.src='https://placehold.co/600x600?text=ShopSphere'\"><div><small>{{p.category_name}}</small><h3>{{p.product_name}}</h3><b>₹{{'%.2f'|format(p.price*(1-p.discount/100))}}</b><p>{{p.stock_quantity}} available</p></div></a><form method=post action='/cart/add/{{p.product_id}}'><button {% if not p.stock_quantity %}disabled{% endif %}>+ Add to bag</button></form></article>{% else %}<p>No products found.</p>{% endfor %}</div>"""
@app.get("/")
def home():
 p=q("SELECT p.*,c.category_name FROM products p JOIN categories c USING(category_id) WHERE active=1 ORDER BY featured DESC,product_id DESC LIMIT 12")
 cats=q("SELECT * FROM categories")
 return page("""<section class=hero><div><small>THE EVERYDAY EDIT · 2026</small><h1>Good things.<br><em>Better living.</em></h1><p>Discover considered essentials, fresh technology and little upgrades that make a difference.</p><a class=btn href=/products>Explore collection ↗</a></div><div class=art>✳</div></section><section class=section><small>HANDPICKED FOR YOU</small><h2>Featured finds</h2>"""+CARD+"""</section><section class=section><h2>Shop by category</h2>{% for c in cats %}<a class=chip href='/products?category={{c.category_id}}'>{{c.category_name}} ↗</a>{% endfor %}</section>""",products=p,cats=cats)
@app.get("/products")
def products():
 term=request.args.get("q","");cat=request.args.get("category","");sql="SELECT p.*,c.category_name FROM products p JOIN categories c USING(category_id) WHERE p.active=1";a=[]
 if term:sql+=" AND p.product_name LIKE %s";a.append("%"+term+"%")
 if cat:sql+=" AND p.category_id=%s";a.append(cat)
 sql+=" ORDER BY "+({"price":"price ASC","name":"product_name ASC"}.get(request.args.get("sort"),"featured DESC,product_id DESC"))
 return page("<section class=section><small>THE COLLECTION</small><h1>Find your favourite.</h1><form><input name=q value='{{term}}' placeholder='Search products'><select name=sort><option value=featured>Featured</option><option value=price>Price low to high</option><option value=name>Name</option></select><button>Filter</button></form>"+CARD+"</section>",products=q(sql,tuple(a)),term=term,title="Discover")
@app.get("/product/<int:pid>")
def product(pid):
 p=q("SELECT p.*,c.category_name FROM products p JOIN categories c USING(category_id) WHERE product_id=%s AND active=1",(pid,),True)
 if not p:return "Not found",404
 return page("""<section class=section columns><img class=detail src='{{p.image_url or "https://placehold.co/700"}}'><div><small>{{p.category_name}}</small><h1>{{p.product_name}}</h1><h2>₹{{'%.2f'|format(p.price*(1-p.discount/100))}}</h2><p>{{p.description}}</p><p>{{p.stock_quantity}} in stock</p><form method=post action='/cart/add/{{p.product_id}}'><input name=qty type=number min=1 max={{p.stock_quantity}} value=1><button>Add to bag</button></form></div></section>""",p=p)
@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  n=request.form["name"].strip();e=request.form["email"].lower().strip();pw=request.form["password"]
  if len(pw)<8:flash("Password must contain at least 8 characters.","error")
  elif q("SELECT uid FROM users WHERE email=%s",(e,),True):flash("Email already exists.","error")
  else:q("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'customer')",(n,e,generate_password_hash(pw)),commit=True);flash("Account created. Sign in.","success");return redirect(url_for("signin"))
 return page("""<section class=section><form class=form method=post><h1>Create account</h1><input name=name placeholder='Full name' required><input name=email type=email placeholder=Email required><input name=password type=password minlength=8 placeholder='Password (8+ characters)' required><button>Register</button></form></section>""")
@app.route("/login",methods=["GET","POST"])
@app.route("/signin",methods=["GET","POST"])
def signin():
 if request.method=="POST":
  u=q("SELECT * FROM users WHERE email=%s",(request.form["email"].lower().strip(),),True)
  if u and check_password_hash(u["password_hash"],request.form["password"]):
   session.clear();session.update(uid=u["uid"],name=u["name"],role=u["role"]);return redirect(url_for("admin_home") if u["role"]=="admin" else url_for("home"))
  flash("Invalid email or password.","error")
 return page("""<section class=section><form class=form method=post><h1>Welcome back.</h1><input name=email type=email placeholder=Email required><input name=password type=password placeholder=Password required><button>Sign in</button></form></section>""")
@app.get("/logout")
def logout():session.clear();return redirect("/")
@app.post("/cart/add/<int:pid>")
def add(pid):
 p=q("SELECT stock_quantity FROM products WHERE product_id=%s AND active=1",(pid,),True)
 if p and p["stock_quantity"]:
  cart=session.get("cart",{});key=str(pid);n=max(1,int(request.form.get("qty",1)));cart[key]={"qty":min(p["stock_quantity"],n+cart.get(key,{}).get("qty",0))};session["cart"]=cart;flash("Added to your bag.","success")
 else:flash("Item is unavailable.","error")
 return redirect(request.referrer or "/products")
@app.get("/cart")
def cart():
 rows=[];total=0
 for pid,x in session.get("cart",{}).items():
  p=q("SELECT * FROM products WHERE product_id=%s",(int(pid),),True)
  if p:
   n=min(x["qty"],p["stock_quantity"]);unit=float(p["price"])*(1-float(p["discount"])/100);sub=round(unit*n,2);total+=sub;rows.append((p,n,sub))
 return page("""<section class=section><h1>Your bag.</h1><form method=post action=/cart/update>{% for p,n,s in rows %}<div class=row><img src='{{p.image_url or "https://placehold.co/100"}}'><div><b>{{p.product_name}}</b><p>₹{{s}}</p><input type=number min=0 max={{p.stock_quantity}} name=qty_{{p.product_id}} value={{n}}></div></div>{% else %}<p>Your bag is empty.</p>{% endfor %}<button>Update quantities</button></form><h2>Total ₹{{'%.2f'|format(total)}}</h2>{% if rows %}<a class=btn href=/checkout>Checkout ↗</a>{% endif %}</section>""",rows=rows,total=total)
@app.post("/cart/update")
def update():
 c=session.get("cart",{})
 for pid in list(c):
  n=int(request.form.get("qty_"+pid,0));p=q("SELECT stock_quantity FROM products WHERE product_id=%s",(int(pid),),True)
  if n<=0 or not p:c.pop(pid,None)
  else:c[pid]={"qty":min(n,p["stock_quantity"])}
 session["cart"]=c;return redirect("/cart")
@app.route("/checkout",methods=["GET","POST"])
@login
def checkout():
 items=[];total=0
 for pid,x in session.get("cart",{}).items():
  p=q("SELECT * FROM products WHERE product_id=%s AND active=1",(int(pid),),True)
  if not p or x["qty"]>p["stock_quantity"]:flash("Stock changed. Update your bag.","error");return redirect("/cart")
  unit=float(p["price"])*(1-float(p["discount"])/100);sub=round(unit*x["qty"],2);items.append((p,x["qty"],sub));total+=sub
 if request.method=="POST":
  c=mysql.connector.connect(**DB);k=c.cursor()
  try:
   c.start_transaction();code="SS-"+uuid.uuid4().hex[:10].upper()
   k.execute("INSERT INTO orders(order_code,user_id,total_amount,shipping_address) VALUES(%s,%s,%s,%s)",(code,session["uid"],total,request.form["address"]));oid=k.lastrowid
   for p,n,s in items:
    k.execute("SELECT stock_quantity FROM products WHERE product_id=%s FOR UPDATE",(p["product_id"],))
    if k.fetchone()[0]<n:raise ValueError("Insufficient stock; review your bag.")
    k.execute("INSERT INTO order_items(order_id,product_id,quantity,unit_price,subtotal) VALUES(%s,%s,%s,%s,%s)",(oid,p["product_id"],n,round(s/n,2),s))
    k.execute("UPDATE products SET stock_quantity=stock_quantity-%s WHERE product_id=%s",(n,p["product_id"]))
   k.execute("INSERT INTO payments(order_id,payment_method,payment_status) VALUES(%s,%s,'Demo only')",(oid,request.form["payment"]))
   c.commit();session["cart"]={};return page("<section class=section><h1>Order confirmed ✓</h1><p>Order {{code}} placed successfully.</p><h2>₹{{total}}</h2><a class=btn href=/account>View orders</a></section>",code=code,total=total)
  except Exception as e:c.rollback();flash(str(e),"error")
  finally:k.close();c.close()
 return page("""<section class=section columns><form class=form method=post><h1>Checkout</h1><textarea name=address placeholder='Delivery address' required></textarea><select name=payment><option>Cash on delivery</option><option>UPI simulated</option><option>Card simulated (no card details)</option></select><button>Place demo order</button><small>No real payment is collected.</small></form><div class=panel><h2>Total ₹{{total}}</h2>{% for p,n,s in items %}<p>{{p.product_name}} × {{n}} — ₹{{s}}</p>{% endfor %}</div></section>""",items=items,total=total)
@app.get("/account")
@login
def account():return page("""<section class=section><h1>Your orders</h1><table><tr><th>Order</th><th>Total</th><th>Status</th><th>Date</th></tr>{% for o in orders %}<tr><td>{{o.order_code}}</td><td>₹{{o.total_amount}}</td><td>{{o.order_status}}</td><td>{{o.created_at}}</td></tr>{% endfor %}</table></section>""",orders=q("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC",(session["uid"],)))
@app.get("/admin")
@admin
def admin_home():
 s=q("SELECT (SELECT COUNT(*) FROM users WHERE role='customer') customers,(SELECT COUNT(*) FROM products WHERE active=1) products,(SELECT COALESCE(SUM(stock_quantity),0) FROM products) stock,(SELECT COUNT(*) FROM orders) orders,(SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE order_status<>'Cancelled') revenue",one=True)
 return page(ADMIN,s=s,orders=q("SELECT o.*,u.name FROM orders o JOIN users u USING(user_id) ORDER BY created_at DESC LIMIT 12"),title="Admin")
ADMIN="""<div class=admin><aside class=side><h2>ShopSphere Admin</h2><a href=/admin>Overview</a><a href=/admin/products>Products & stock</a><a href=/admin/orders>Orders</a><a href=/admin/analytics>Analytics</a><a href=/admin/lab>Data Analysis Lab</a><a href=/admin/csv>CSV centre</a><a href=/>Storefront</a></aside><section class=content><small>LIVE STORE METRICS</small><h1>Dashboard</h1><div class=stats>{% for k,v in [('Customers',s.customers),('Products',s.products),('Stock units',s.stock),('Orders',s.orders),('Revenue','₹%.2f'|format(s.revenue))] %}<div class=stat>{{k}}<b>{{v}}</b></div>{% endfor %}</div><h2>Recent orders</h2><table><tr><th>Order</th><th>Customer</th><th>Amount</th><th>Status</th></tr>{% for o in orders %}<tr><td>{{o.order_code}}</td><td>{{o.name}}</td><td>{{o.total_amount}}</td><td>{{o.order_status}}</td></tr>{% endfor %}</table></section></div>"""
@app.get("/admin/products")
@admin
def manage_products():return page("""<div class=admin><aside class=side><h2>Admin</h2><a href=/admin>Overview</a><a href=/admin/products>Products</a><a href=/admin/orders>Orders</a><a href=/admin/analytics>Analytics</a><a href=/admin/lab>Data Lab</a><a href=/admin/csv>CSV</a></aside><section class=content><h1>Products & inventory</h1><form class=form method=post action=/admin/products><input name=product_name placeholder='Product name' required><select name=category_id>{% for c in cats %}<option value={{c.category_id}}>{{c.category_name}}</option>{% endfor %}</select><input name=price type=number step=.01 placeholder=Price required><input name=discount type=number value=0 placeholder='Discount %'><input name=stock type=number placeholder=Stock required><input name=image_url placeholder='Image URL'><textarea name=description placeholder=Description></textarea><button>Add product</button></form><table><tr><th>Product</th><th>Price</th><th>Stock</th><th>Action</th></tr>{% for p in products %}<tr><td>{{p.product_name}}</td><td>{{p.price}}</td><td>{{p.stock_quantity}}</td><td><form method=post action='/admin/products/{{p.product_id}}/delete'><button>Archive</button></form></td></tr>{% endfor %}</table></section></div>""",cats=q("SELECT * FROM categories"),products=q("SELECT * FROM products WHERE active=1"))
@app.post("/admin/products")
@admin
def add_product():
 d=(request.form["product_name"],int(request.form["category_id"]),request.form.get("description",""),float(request.form["price"]),float(request.form.get("discount",0)),int(request.form["stock"]),request.form.get("image_url",""))
 if d[3]<0 or not 0<=d[4]<=90 or d[5]<0:flash("Invalid price, discount or stock.","error")
 else:q("INSERT INTO products(product_name,category_id,description,price,discount,stock_quantity,image_url) VALUES(%s,%s,%s,%s,%s,%s,%s)",d,commit=True);flash("Product created.","success")
 return redirect("/admin/products")
@app.post("/admin/products/<int:pid>/delete")
@admin
def archive(pid):q("UPDATE products SET active=0 WHERE product_id=%s",(pid,),commit=True);return redirect("/admin/products")
@app.get("/admin/orders")
@admin
def manage_orders():return page("""<div class=admin><aside class=side><h2>Admin</h2><a href=/admin>Overview</a><a href=/admin/products>Products</a><a href=/admin/orders>Orders</a><a href=/admin/analytics>Analytics</a><a href=/admin/lab>Data Lab</a><a href=/admin/csv>CSV</a></aside><section class=content><h1>Order management</h1><table><tr><th>Order</th><th>Customer</th><th>Total</th><th>Status / update</th></tr>{% for o in orders %}<tr><td>{{o.order_code}}</td><td>{{o.name}}</td><td>{{o.total_amount}}</td><td><form method=post action='/admin/orders/{{o.order_id}}'><select name=status>{% for x in ['Placed','Processing','Shipped','Delivered','Cancelled'] %}<option {% if x==o.order_status %}selected{% endif %}>{{x}}</option>{% endfor %}</select><button>Save</button></form></td></tr>{% endfor %}</table></section></div>""",orders=q("SELECT o.*,u.name FROM orders o JOIN users u USING(user_id) ORDER BY created_at DESC"))
@app.post("/admin/orders/<int:oid>")
@admin
def status(oid):
 x=request.form["status"]
 if x in ["Placed","Processing","Shipped","Delivered","Cancelled"]:q("UPDATE orders SET order_status=%s WHERE order_id=%s",(x,oid),commit=True)
 return redirect("/admin/orders")
def frame():
 d=pd.DataFrame(q("SELECT p.product_name,c.category_name,oi.quantity,oi.subtotal,o.created_at FROM order_items oi JOIN orders o USING(order_id) JOIN products p USING(product_id) JOIN categories c USING(category_id) WHERE o.order_status<>'Cancelled'"))
 if len(d):d["month"]=pd.to_datetime(d.created_at).dt.to_period("M").astype(str)
 return d
@app.get("/admin/analytics")
@admin
def analytics():d=frame();return page("""<div class=admin><aside class=side><h2>Admin</h2><a href=/admin>Overview</a><a href=/admin/products>Products</a><a href=/admin/orders>Orders</a><a href=/admin/analytics>Analytics</a><a href=/admin/lab>Data Lab</a><a href=/admin/csv>CSV</a></aside><section class=content><h1>Business intelligence</h1><p>{{n}} sales rows · Mean line revenue ₹{{avg}}</p>{% for t in ['monthly','category','top'] %}<div class=panel><h3>{{t|title}}</h3><img class=chart src='/admin/chart/{{t}}.png'></div>{% endfor %}</section></div>""",n=len(d),avg=round(float(d.subtotal.mean()),2) if len(d) else 0)
@app.get("/admin/chart/<kind>.png")
@admin
def chart(kind):
 d=frame();fig,ax=plt.subplots(figsize=(8,4))
 if not len(d):ax.text(.5,.5,"No sales data yet",ha="center")
 elif kind=="monthly":d.groupby("month").subtotal.sum().plot(ax=ax,marker="o")
 elif kind=="category":d.groupby("category_name").subtotal.sum().plot(kind="bar",ax=ax)
 elif kind=="top":d.groupby("product_name").quantity.sum().nlargest(5).sort_values().plot(kind="barh",ax=ax)
 else:return "Not found",404
 fig.tight_layout();b=io.BytesIO();fig.savefig(b,format="png");plt.close(fig);b.seek(0);return send_file(b,mimetype="image/png")
@app.get("/admin/lab")
@admin
def lab():
 d=pd.DataFrame(q("SELECT product_name,price,stock_quantity FROM products WHERE active=1"));s=pd.Series(d.price.values,index=d.product_name) if len(d) else pd.Series(dtype=float)
 return page("""<div class=admin><aside class=side><h2>Admin</h2><a href=/admin>Overview</a><a href=/admin/products>Products</a><a href=/admin/orders>Orders</a><a href=/admin/analytics>Analytics</a><a href=/admin/lab>Data Lab</a><a href=/admin/csv>CSV</a></aside><section class=content><small>CBSE CLASS XII INFORMATICS PRACTICES</small><h1>Data Analysis Lab</h1><div class=stats><div class=stat>Series mean<b>₹{{mean}}</b></div><div class=stat>Series max<b>₹{{maximum}}</b></div><div class=stat>DataFrame rows<b>{{count}}</b></div></div><div class=panel>{{table|safe}}</div><pre>SELECT category_id, SUM(stock_quantity) FROM products GROUP BY category_id;</pre></section></div>""",mean=round(float(s.mean()),2) if len(s) else 0,maximum=float(s.max()) if len(s) else 0,count=len(d),table=d.head(15).to_html(index=False,classes="data-table"))
@app.get("/admin/csv")
@admin
def csvpage():return page("""<div class=admin><aside class=side><h2>Admin</h2><a href=/admin>Overview</a><a href=/admin/products>Products</a><a href=/admin/orders>Orders</a><a href=/admin/analytics>Analytics</a><a href=/admin/lab>Data Lab</a><a href=/admin/csv>CSV</a></aside><section class=content><h1>CSV import & export</h1><div class=panel><form method=post enctype=multipart/form-data><p>Required columns: product_name, category_id, price, stock_quantity</p><input type=file name=file accept=.csv required><button>Validate & import</button></form></div><div class=panel><a href=/admin/export/products.csv>Products CSV</a> · <a href=/admin/export/orders.csv>Orders CSV</a> · <a href=/admin/export/customers.csv>Customers CSV</a> · <a href=/admin/export/inventory.csv>Inventory CSV</a></div></section></div>""")
@app.post("/admin/csv")
@admin
def csvimport():
 try:
  d=pd.read_csv(request.files["file"]).fillna("");required={"product_name","category_id","price","stock_quantity"}
  if not required.issubset(d.columns):raise ValueError("CSV is missing required columns")
  for _,r in d.iterrows():q("INSERT INTO products(product_name,category_id,price,stock_quantity,description,discount,image_url) VALUES(%s,%s,%s,%s,%s,%s,%s)",(str(r.product_name),int(r.category_id),float(r.price),int(r.stock_quantity),str(r.get("description","")),float(r.get("discount",0) or 0),str(r.get("image_url",""))),commit=True)
  flash("CSV imported.","success")
 except Exception as e:flash("Import failed: "+str(e),"error")
 return redirect("/admin/csv")
@app.get("/admin/export/<kind>.csv")
@admin
def export(kind):
 sql={"products":"SELECT product_id,product_name,category_id,price,discount,stock_quantity FROM products","orders":"SELECT order_code,user_id,total_amount,order_status,created_at FROM orders","customers":"SELECT uid,name,email,created_at FROM users WHERE role='customer'","inventory":"SELECT product_id,product_name,stock_quantity FROM products"}
 if kind not in sql:return "Not found",404
 b=io.BytesIO(pd.DataFrame(q(sql[kind])).to_csv(index=False).encode("utf-8-sig"));return send_file(b,mimetype="text/csv",as_attachment=True,download_name=kind+".csv")
if __name__=="__main__":app.run(port=int(os.getenv("PORT",5000)),debug=os.getenv("FLASK_DEBUG")=="1")
