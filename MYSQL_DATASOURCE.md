# MySQL 测试数据源配置

## 数据源 1 (Source)

```
连接名称：MySQL Source (db_source1)
数据库类型：MySQL
主机：localhost
端口：3306
数据库：db_source1
用户名：dbuser
密码：dbpassword123
```

## 数据源 2 (Target)

```
连接名称：MySQL Target (db_source2)
数据库类型：MySQL
主机：localhost
端口：3307
数据库：db_source2
用户名：dbuser
密码：dbpassword123
```

## 表结构差异说明

两个数据源的表结构设计有意的差异，用于测试 Schema 比对功能：

| 表名 | db_source1 | db_source2 | 差异 |
|------|------------|------------|------|
| users | 无 phone 字段 | 有 phone 字段 | source2 多一个字段 |
| products | 无 weight 字段 | 有 weight 字段 | source2 多一个字段 |
| orders | 相同 | 相同 | - |
| order_items | 相同 | 相同 | - |
| system_config | 不存在 | 存在 | source2 独有的表 |

## 测试数据

- **users**: source1 有 3 条记录 (admin, user1, user2)，source2 有 3 条记录 (admin, user1, user3)
- **products**: source1 有 4 条记录，source2 有 5 条记录 (多一个 Apple Watch S9)
- **orders**: source1 有 3 条订单，source2 有 2 条订单
- **order_items**: source1 有 4 条明细，source2 有 3 条明细

## Docker 容器信息

```bash
# 查看运行状态
docker ps | grep mysql

# 容器 1: docker-mysql1-1 (端口 3306)
# 容器 2: docker-mysql2-1 (端口 3307)

# 停止容器
docker stop docker-mysql1-1 docker-mysql2-1

# 启动容器
docker start docker-mysql1-1 docker-mysql2-1

# 重新初始化数据
docker exec -i docker-mysql1-1 mysql -u root -proot < scripts/init_mysql.sql
docker exec -i docker-mysql2-1 mysql -u root -proot < scripts/init_mysql.sql
```

## 快速连接步骤

1. 启动项目：`./scripts/start.sh`
2. 访问前端：http://localhost:5173
3. 点击 "Connections" 标签
4. 添加第一个连接 (Source):
   - Name: MySQL Source
   - Type: MySQL
   - Host: localhost
   - Port: 3306
   - Database: db_source1
   - Username: dbuser
   - Password: dbpassword123
5. 添加第二个连接 (Target):
   - Name: MySQL Target
   - Type: MySQL
   - Host: localhost
   - Port: 3307
   - Database: db_source2
   - Username: dbuser
   - Password: dbpassword123
6. 切换到 "Schema Comparison" 标签进行比对
