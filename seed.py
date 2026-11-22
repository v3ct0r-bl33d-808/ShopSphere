import os
from werkzeug.security import generate_password_hash
import mysql.connector
c=mysql.connector.connect(host=os.getenv("DB_HOST","127.0.0.1"),user=os.getenv("DB_USER","root"),password=os.getenv("DB_PASSWORD",""),database=os.getenv("DB_NAME","shopsphere_db"));k=c.cursor()
products=[("Wireless headphones",1,2499,10,24),("Minimal wrist watch",8,1899,5,19),("Everyday backpack",2,1599,12,20),("Ceramic coffee mug",4,499,0,42),("Desk lamp",4,1299,8,16),("Classic novel",3,399,0,60),("Yoga mat",5,899,5,27),("Notebook set",6,299,0,80),("Sunglasses",8,799,15,25),("Skincare kit",7,1199,10,14)]
for i in range(40):
 n,cat,price,discount,stock=products[i%10]
 k.execute("INSERT INTO products(product_name,category_id,description,price,discount,stock_quantity,featured) VALUES(%s,%s,%s,%s,%s,%s,%s)",(n+(" "+str(i//10+1) if i>=10 else ""),cat,"ShopSphere demonstration product.",price,discount,stock,int(i<8)))
k.execute("INSERT IGNORE INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'admin')",("ShopSphere Admin",os.getenv("ADMIN_EMAIL","admin@shopsphere.demo"),generate_password_hash(os.getenv("ADMIN_PASSWORD","ChangeMe123!"))))
c.commit();k.close();c.close();print("40 products seeded. Demo admin: admin@shopsphere.demo; change password before use.")
