# Text2SQL 评估报告

生成时间: 2025-06-12 18:46:27

## 总体评估
- 总样本数: 36
- SQL生成成功: 36
- SQL生成失败: 0
- SQL执行成功: 9
- SQL执行失败: 0
- 平均语法相似度: 0.7892
- 平均执行精确率: 0.2222
- 平均执行召回率: 0.2222
- 平均执行F1分数: 0.2222

## 详细结果

### 样本 1
**问题**: List all actors with their IDs and names.
**真实SQL**: SELECT actor_id, first_name, last_name FROM actor;
**预测SQL**: SELECT actor_id, first_name, last_name FROM actor;
**语法相似度**: 1.0000
**执行结果**: P=1.0000, R=1.0000, F1=1.0000

### 样本 2
**问题**: Add a new actor named 'John Doe'.
**真实SQL**: INSERT INTO actor (first_name, last_name) VALUES ('John', 'Doe');
**预测SQL**: INSERT INTO actor (first_name, last_name) VALUES ('John', 'Doe');
**语法相似度**: 1.0000

### 样本 3
**问题**: Update the last name of actor with ID 1 to 'Smith'.
**真实SQL**: UPDATE actor SET last_name = 'Smith' WHERE actor_id = 1;
**预测SQL**: UPDATE actor SET last_name = 'Smith', last_update = CURRENT_TIMESTAMP WHERE actor_id = 1;
**语法相似度**: 0.6667

### 样本 4
**问题**: Delete the actor with ID 2.
**真实SQL**: DELETE FROM actor WHERE actor_id = 2;
**预测SQL**: DELETE FROM actor WHERE actor_id = 2;
**语法相似度**: 1.0000

### 样本 5
**问题**: Show all films and their descriptions.
**真实SQL**: SELECT film_id, title, description FROM film;
**预测SQL**: SELECT f.title, f.description 
FROM film f;
**语法相似度**: 0.2000
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 6
**问题**: Insert a new film titled 'New Movie' in language 1.
**真实SQL**: INSERT INTO film (title, language_id) VALUES ('New Movie', 1);
**预测SQL**: INSERT INTO film (title, language_id) VALUES ('New Movie', 1);
**语法相似度**: 1.0000

### 样本 7
**问题**: Change the rating of film ID 3 to 'PG-13'.
**真实SQL**: UPDATE film SET rating = 'PG-13' WHERE film_id = 3;
**预测SQL**: UPDATE film SET rating = 'PG-13' WHERE film_id = 3;
**语法相似度**: 1.0000

### 样本 8
**问题**: Remove the film with ID 4.
**真实SQL**: DELETE FROM film WHERE film_id = 4;
**预测SQL**: DELETE FROM film WHERE film_id = 4;
**语法相似度**: 1.0000

### 样本 9
**问题**: Retrieve all categories.
**真实SQL**: SELECT category_id, name FROM category;
**预测SQL**: SELECT * FROM category;
**语法相似度**: 0.5000
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 10
**问题**: Add a new category 'Horror'.
**真实SQL**: INSERT INTO category (name) VALUES ('Horror');
**预测SQL**: INSERT INTO category (name) VALUES ('Horror');
**语法相似度**: 1.0000

### 样本 11
**问题**: Rename category ID 5 to 'Thriller'.
**真实SQL**: UPDATE category SET name = 'Thriller' WHERE category_id = 5;
**预测SQL**: UPDATE category SET name = 'Thriller', last_update = CURRENT_TIMESTAMP WHERE category_id = 5;
**语法相似度**: 0.6667

### 样本 12
**问题**: Delete category with ID 6.
**真实SQL**: DELETE FROM category WHERE category_id = 6;
**预测SQL**: DELETE FROM category WHERE category_id = 6;
**语法相似度**: 1.0000

### 样本 13
**问题**: List all customers with their store and email.
**真实SQL**: SELECT customer_id, store_id, email FROM customer;
**预测SQL**: SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    s.store_id,
    st.first_name AS manager_first_name,
    st.last_name AS manager_last_name
FROM 
    customer c
JOIN 
    store s ON c.store_id = s.store_id
JOIN 
    staff st ON s.manager_staff_id = st.staff_id;
**语法相似度**: 0.0690
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 14
**问题**: Create a new customer for store 1 named 'Alice Brown'.
**真实SQL**: INSERT INTO customer (store_id, first_name, last_name, create_date, address_id, active) VALUES (1, 'Alice', 'Brown', NOW(), 1, 1);
**预测SQL**: INSERT INTO customer (store_id, first_name, last_name, active) VALUES (1, 'Alice', 'Brown', 1);
**语法相似度**: 0.7500

### 样本 15
**问题**: Update email of customer ID 10 to 'newemail@example.com'.
**真实SQL**: UPDATE customer SET email = 'newemail@example.com' WHERE customer_id = 10;
**预测SQL**: UPDATE customer SET email = 'newemail@example.com' WHERE customer_id = 10;
**语法相似度**: 1.0000

### 样本 16
**问题**: Remove customer with ID 11.
**真实SQL**: DELETE FROM customer WHERE customer_id = 11;
**预测SQL**: DELETE FROM customer WHERE customer_id = 11;
**语法相似度**: 1.0000

### 样本 17
**问题**: Show inventory items for film ID 5.
**真实SQL**: SELECT inventory_id, film_id, store_id FROM inventory WHERE film_id = 5;
**预测SQL**: SELECT * FROM inventory WHERE film_id = 5;
**语法相似度**: 0.6364
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 18
**问题**: Add a new inventory item for film 5 in store 2.
**真实SQL**: INSERT INTO inventory (film_id, store_id) VALUES (5, 2);
**预测SQL**: INSERT INTO inventory (film_id, store_id) VALUES (5, 2);
**语法相似度**: 1.0000

### 样本 19
**问题**: Update the store of inventory ID 20 to store 3.
**真实SQL**: UPDATE inventory SET store_id = 3 WHERE inventory_id = 20;
**预测SQL**: UPDATE inventory SET store_id = 3 WHERE inventory_id = 20;
**语法相似度**: 1.0000

### 样本 20
**问题**: Delete inventory record with ID 21.
**真实SQL**: DELETE FROM inventory WHERE inventory_id = 21;
**预测SQL**: DELETE FROM inventory WHERE inventory_id = 21;
**语法相似度**: 1.0000

### 样本 21
**问题**: List recent rentals with rental date and customer.
**真实SQL**: SELECT rental_id, rental_date, customer_id FROM rental ORDER BY rental_date DESC LIMIT 10;
**预测SQL**: SELECT r.rental_id, r.rental_date, r.customer_id 
FROM rental r 
ORDER BY r.rental_date DESC 
LIMIT 10;
**语法相似度**: 0.4706
**执行结果**: P=1.0000, R=1.0000, F1=1.0000

### 样本 22
**问题**: Record a new rental for inventory 15 by customer 5.
**真实SQL**: INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id) VALUES (NOW(), 15, 5, 1);
**预测SQL**: INSERT INTO rental (rental_date, inventory_id, customer_id, return_date, staff_id) 
VALUES (CURRENT_TIMESTAMP, 15, 5, NULL, NULL);
**语法相似度**: 0.6250

### 样本 23
**问题**: Update return date for rental ID 3 to current time.
**真实SQL**: UPDATE rental SET return_date = NOW() WHERE rental_id = 3;
**预测SQL**: UPDATE rental SET return_date = CURRENT_TIMESTAMP WHERE rental_id = 3;
**语法相似度**: 0.8000

### 样本 24
**问题**: Remove the rental record with ID 4.
**真实SQL**: DELETE FROM rental WHERE rental_id = 4;
**预测SQL**: DELETE FROM rental WHERE rental_id = 4;
**语法相似度**: 1.0000

### 样本 25
**问题**: Show all payments with amount and date.
**真实SQL**: SELECT payment_id, customer_id, amount, payment_date FROM payment;
**预测SQL**: SELECT amount, payment_date FROM payment;
**语法相似度**: 0.7143
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 26
**问题**: Add a payment of 9.99 for rental 3 by customer 5.
**真实SQL**: INSERT INTO payment (customer_id, staff_id, rental_id, amount, payment_date) VALUES (5, 1, 3, 9.99, NOW());
**预测SQL**: INSERT INTO payment (customer_id, rental_id, amount) VALUES (5, 3, 9.99);
**语法相似度**: 0.5000

### 样本 27
**问题**: Change payment amount of payment ID 6 to 12.50.
**真实SQL**: UPDATE payment SET amount = 12.50 WHERE payment_id = 6;
**预测SQL**: UPDATE payment SET amount = 12.50 WHERE payment_id = 6;
**语法相似度**: 1.0000

### 样本 28
**问题**: Delete payment record with ID 7.
**真实SQL**: DELETE FROM payment WHERE payment_id = 7;
**预测SQL**: DELETE FROM payment WHERE payment_id = 7;
**语法相似度**: 1.0000

### 样本 29
**问题**: List all staff with names and email.
**真实SQL**: SELECT staff_id, first_name, last_name, email FROM staff;
**预测SQL**: SELECT s.first_name, s.last_name, s.email
FROM staff s;
**语法相似度**: 0.1667
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 30
**问题**: Hire a new staff member 'Bob Lee' at store 1.
**真实SQL**: INSERT INTO staff (first_name, last_name, address_id, store_id, active, username) VALUES ('Bob', 'Lee', 1, 1, 1, 'boblee');
**预测SQL**: INSERT INTO staff (first_name, last_name, store_id, username, active) VALUES ('Bob', 'Lee', 1, 'boblee', 1);
**语法相似度**: 0.5556

### 样本 31
**问题**: Deactivate staff with ID 2.
**真实SQL**: UPDATE staff SET active = 0 WHERE staff_id = 2;
**预测SQL**: UPDATE staff SET active = 0 WHERE staff_id = 2;
**语法相似度**: 1.0000

### 样本 32
**问题**: Remove staff member with ID 3.
**真实SQL**: DELETE FROM staff WHERE staff_id = 3;
**预测SQL**: DELETE FROM staff WHERE staff_id = 3;
**语法相似度**: 1.0000

### 样本 33
**问题**: Show all stores with manager and address.
**真实SQL**: SELECT store_id, manager_staff_id, address_id FROM store;
**预测SQL**: SELECT 
    s.store_id,
    s.manager_staff_id,
    a.address,
    a.address2,
    a.district,
    a.postal_code,
    a.phone
FROM 
    store s
JOIN 
    address a ON s.address_id = a.address_id;
**语法相似度**: 0.0909
**执行结果**: P=0.0000, R=0.0000, F1=0.0000

### 样本 34
**问题**: Open a new store with manager 2 at address 3.
**真实SQL**: INSERT INTO store (manager_staff_id, address_id) VALUES (2, 3);
**预测SQL**: INSERT INTO store (manager_staff_id, address_id) VALUES (2, 3);
**语法相似度**: 1.0000

### 样本 35
**问题**: Change manager of store ID 2 to staff ID 4.
**真实SQL**: UPDATE store SET manager_staff_id = 4 WHERE store_id = 2;
**预测SQL**: UPDATE store SET manager_staff_id = 4 WHERE store_id = 2;
**语法相似度**: 1.0000

### 样本 36
**问题**: Close (delete) store with ID 3.
**真实SQL**: DELETE FROM store WHERE store_id = 3;
**预测SQL**: DELETE FROM store WHERE store_id = 3;
**语法相似度**: 1.0000