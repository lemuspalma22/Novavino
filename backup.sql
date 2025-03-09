-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: localhost    Database: crm_db
-- ------------------------------------------------------
-- Server version	8.0.36

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `crm_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `crm_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `railway`;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add factura',7,'add_factura'),(26,'Can change factura',7,'change_factura'),(27,'Can delete factura',7,'delete_factura'),(28,'Can view factura',7,'view_factura'),(29,'Can add compra',8,'add_compra'),(30,'Can change compra',8,'change_compra'),(31,'Can delete compra',8,'delete_compra'),(32,'Can view compra',8,'view_compra'),(33,'Can add empresa',9,'add_empresa'),(34,'Can change empresa',9,'change_empresa'),(35,'Can delete empresa',9,'delete_empresa'),(36,'Can view empresa',9,'view_empresa'),(37,'Can add proveedor',10,'add_proveedor'),(38,'Can change proveedor',10,'change_proveedor'),(39,'Can delete proveedor',10,'delete_proveedor'),(40,'Can view proveedor',10,'view_proveedor'),(41,'Can add compra producto',11,'add_compraproducto'),(42,'Can change compra producto',11,'change_compraproducto'),(43,'Can delete compra producto',11,'delete_compraproducto'),(44,'Can view compra producto',11,'view_compraproducto'),(45,'Can add producto',12,'add_producto'),(46,'Can change producto',12,'change_producto'),(47,'Can delete producto',12,'delete_producto'),(48,'Can view producto',12,'view_producto'),(49,'Can add inventario',13,'add_inventario'),(50,'Can change inventario',13,'change_inventario'),(51,'Can delete inventario',13,'delete_inventario'),(52,'Can view inventario',13,'view_inventario'),(53,'Can add producto',14,'add_producto'),(54,'Can change producto',14,'change_producto'),(55,'Can delete producto',14,'delete_producto'),(56,'Can view producto',14,'view_producto'),(57,'Can add pago factura',15,'add_pagofactura'),(58,'Can change pago factura',15,'change_pagofactura'),(59,'Can delete pago factura',15,'delete_pagofactura'),(60,'Can view pago factura',15,'view_pagofactura'),(61,'Can add detalle factura',16,'add_detallefactura'),(62,'Can change detalle factura',16,'change_detallefactura'),(63,'Can delete detalle factura',16,'delete_detallefactura'),(64,'Can view detalle factura',16,'view_detallefactura');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$870000$Mmo2ItgiyT8QXAy5K7sRwh$P26GY56a1chvjeCrz/2yqi9ymxzThYZskgQtTXXdlak=',NULL,1,'lenovo','','','rlemusnovavino@gmail.com',1,1,'2024-10-31 05:57:16.753065'),(2,'pbkdf2_sha256$870000$WCg9cONJd5Ep0dKEXXvwpa$V8ZzWyKptSW4oT5mmmd6DHjJPU9JmRGuK/xL3YLmA7k=','2025-02-18 06:26:05.960431',1,'rodrigo.lemus','','','rlemusnovavino@gmail.com',1,1,'2024-10-31 06:05:59.476601');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras_compra`
--

DROP TABLE IF EXISTS `compras_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras_compra` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `folio` varchar(20) NOT NULL,
  `fecha` date NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `revision` tinyint(1) NOT NULL,
  `archivo` varchar(100) DEFAULT NULL,
  `pagado` tinyint(1) NOT NULL,
  `fecha_pago` date DEFAULT NULL,
  `complemento_pago` varchar(100) DEFAULT NULL,
  `notas` longtext,
  `proveedor_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `compras_compra_proveedor_id_d647dfa3_fk_compras_proveedor_id` (`proveedor_id`),
  CONSTRAINT `compras_compra_proveedor_id_d647dfa3_fk_compras_proveedor_id` FOREIGN KEY (`proveedor_id`) REFERENCES `compras_proveedor` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras_compra`
--

LOCK TABLES `compras_compra` WRITE;
/*!40000 ALTER TABLE `compras_compra` DISABLE KEYS */;
INSERT INTO `compras_compra` VALUES (1,'435','2024-11-01',325.65,0,'',0,NULL,NULL,'',1);
/*!40000 ALTER TABLE `compras_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras_compraproducto`
--

DROP TABLE IF EXISTS `compras_compraproducto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras_compraproducto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `compra_id` bigint NOT NULL,
  `producto_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `compras_compraproducto_compra_id_9400aab4_fk_compras_compra_id` (`compra_id`),
  KEY `compras_compraproduc_producto_id_779c8a0b_fk_compras_p` (`producto_id`),
  CONSTRAINT `compras_compraproduc_producto_id_779c8a0b_fk_compras_p` FOREIGN KEY (`producto_id`) REFERENCES `compras_producto` (`id`),
  CONSTRAINT `compras_compraproducto_compra_id_9400aab4_fk_compras_compra_id` FOREIGN KEY (`compra_id`) REFERENCES `compras_compra` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras_compraproducto`
--

LOCK TABLES `compras_compraproducto` WRITE;
/*!40000 ALTER TABLE `compras_compraproducto` DISABLE KEYS */;
/*!40000 ALTER TABLE `compras_compraproducto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras_producto`
--

DROP TABLE IF EXISTS `compras_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras_producto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  `proveedor_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `compras_producto_proveedor_id_84617c1c_fk_compras_proveedor_id` (`proveedor_id`),
  CONSTRAINT `compras_producto_proveedor_id_84617c1c_fk_compras_proveedor_id` FOREIGN KEY (`proveedor_id`) REFERENCES `compras_proveedor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras_producto`
--

LOCK TABLES `compras_producto` WRITE;
/*!40000 ALTER TABLE `compras_producto` DISABLE KEYS */;
/*!40000 ALTER TABLE `compras_producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras_proveedor`
--

DROP TABLE IF EXISTS `compras_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras_proveedor` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras_proveedor`
--

LOCK TABLES `compras_proveedor` WRITE;
/*!40000 ALTER TABLE `compras_proveedor` DISABLE KEYS */;
INSERT INTO `compras_proveedor` VALUES (3,'Cosecha'),(8,'La Puerta del Sol'),(1,'LCV'),(7,'Mezquite'),(5,'Pinord'),(4,'Secretos de la vid'),(6,'Tannico'),(10,'Uby'),(2,'Vieja Bodega'),(9,'Vita de Vie');
/*!40000 ALTER TABLE `compras_proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2024-10-31 06:10:49.795339','1','Factura 123 - Cliente: MMRE',1,'[{\"added\": {}}]',7,2),(2,'2024-11-02 02:02:40.869592','1','LCV',1,'[{\"added\": {}}]',9,2),(3,'2024-11-02 02:03:15.331877','1','Compra 4672 - Empresa: LCV - Estado: Viva',1,'[{\"added\": {}}]',8,2),(4,'2024-11-02 02:42:50.350313','1','LCV',1,'[{\"added\": {}}]',10,2),(5,'2024-11-02 02:56:26.269498','1','LCV',1,'[{\"added\": {}}]',10,2),(6,'2024-11-02 02:56:43.945669','1','Compra 435 - Proveedor: LCV - Estado: Viva',1,'[{\"added\": {}}]',8,2),(7,'2025-02-05 04:43:25.245263','348','Ginebra Marconi 46 Poli - Sin tipo definido',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(8,'2025-02-05 04:51:28.506783','213','Altotinto Elite Albarino - Sin tipo definido',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(9,'2025-02-05 04:52:05.270853','214','Altotinto Elite Nebbiolo (22 meses) - Sin tipo definido',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(10,'2025-02-05 04:52:43.286204','215','Altotinto Elite Tannat (22 meses) - Sin tipo definido',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(11,'2025-02-05 04:53:11.615882','216','Altotinto Elite Malbec (22 meses) - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(12,'2025-02-05 04:53:54.589664','217','Alto Tinto Elite Blend 10 uvas (22 ms) - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(13,'2025-02-05 04:54:35.490720','229','Unico Santo Tomas G Rva - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(14,'2025-02-05 04:55:23.517161','137','Protos Reserva (Ribera del Duero) - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(15,'2025-02-05 04:56:07.689901','301','Colpo Di Zappa Leone Di Castris - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(16,'2025-02-05 04:56:36.293793','302','Perlui Leone Di Castris (Puglia DOC) - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(17,'2025-02-05 04:57:28.800637','314','Ivan Dolac Ecologico Organico 2010 - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(18,'2025-02-05 04:58:02.856059','315','Dingac 50 - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(19,'2025-02-05 04:58:49.216779','345','Cossy 1er cru - Sin tipo definido',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Precio venta\"]}}]',14,2),(20,'2025-02-05 05:16:27.487450','11','',3,'',10,2),(21,'2025-02-05 05:18:57.516148','270','Viceversa Roble (Navarra) - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Proveedor\"]}}]',14,2),(22,'2025-02-05 05:21:59.851117','275','Laus Barrica (Somontano) - tinto',2,'[{\"changed\": {\"fields\": [\"Tipo\", \"Proveedor\"]}}]',14,2),(23,'2025-02-05 05:27:16.259197','122','Viceversa Roble (Navarra) - Tinto',3,'',14,2),(24,'2025-02-05 05:27:47.329505','127','Laus Barrica (Somontano) - Tinto',3,'',14,2),(25,'2025-02-05 05:28:29.992981','12','Tinto',3,'',10,2),(26,'2025-02-05 05:30:57.126942','2','Vieja Bodega',2,'[{\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Blend (Santo Tomas) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Primeros Pasos (4 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Chardonnay( 9 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Seleccion (Medalla Oro CB) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Gran Cabernet (18 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Alta Reserva (20 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Blend (Santo Tomas) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Primeros Pasos (4 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Chardonnay( 9 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Seleccion (Medalla Oro CB) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Gran Cabernet (18 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Alta Reserva (20 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Blend (Santo Tomas) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Primeros Pasos (4 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Chardonnay( 9 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Seleccion (Medalla Oro CB) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Gran Cabernet (18 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Alta Reserva (20 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Elite Albarino - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Elite Nebbiolo (22 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Elite Tannat (22 meses) - Sin tipo definido\", \"fields\": [\"Tipo\", \"Precio venta\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Elite Malbec (22 meses) - Sin tipo definido\", \"fields\": [\"Tipo\", \"Precio venta\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Elite Blend 10 uvas (22 ms) - Sin tipo definido\", \"fields\": [\"Nombre\", \"Tipo\", \"Precio venta\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Alto Tinto Cosecha Tardia 500 ml - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Reserva familiar Montes Toscanini - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Reserva familiar Montes Toscanini - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Elegido Reserva Montes Toscanini - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Carlos Montes Criado En Roble 12M - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Carlos Montes Criado En Roble 12M - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Carlos Montes Criado En Roble 12M - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"MT Criado en Roble 15 meses - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Corte Supremo Premium 18 meses - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Crudo Barricado Montes T. 8 meses - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota SB - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Chardonnay Chenin Blanc - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota CM - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Blend (Santo Tomas) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Anecdota Primeros Pasos (4 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Chardonnay( 9 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Seleccion (Medalla Oro CB) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto (Valle Sto Tomas 15 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Gran Cabernet (18 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Alta Reserva (20 meses) - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Alto Tinto Cosecha Tardia 500 ml - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Reserva familiar Montes Toscanini - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Reserva familiar Montes Toscanini - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Elegido Reserva Montes Toscanini - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Carlos Montes Criado En Roble 12M - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Carlos Montes Criado En Roble 12M - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Carlos Montes Criado En Roble 12M - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"MT Criado en Roble 15 meses - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Corte Supremo Premium 18 meses - Sin tipo definido\", \"fields\": [\"Tipo\"]}}, {\"changed\": {\"name\": \"producto\", \"object\": \"Crudo Barricado Montes T. 8 meses - Sin tipo definido\", \"fields\": [\"Tipo\"]}}]',10,2),(27,'2025-02-05 05:39:42.131936','2','Vieja Bodega',2,'[{\"changed\": {\"name\": \"producto\", \"object\": \"Altotinto Elite Nebbiolo (22 meses) - tinto\", \"fields\": [\"Tipo\", \"Precio venta\"]}}]',10,2),(28,'2025-02-05 05:41:37.556843','214','Altotinto Elite Nebbiolo (22 meses) - Sin tipo definido',3,'',14,2),(29,'2025-02-07 04:49:24.972609','7','Altotinto Chardonnay( 9 meses) - blanco',2,'[{\"changed\": {\"fields\": [\"Tipo\"]}}]',14,2),(30,'2025-02-07 04:50:41.881449','217','Altotinto Elite Blend 10 uvas (22 ms) - tinto',2,'[{\"changed\": {\"fields\": [\"Nombre\"]}}]',14,2),(31,'2025-02-07 04:53:35.560662','7','Altotinto Chardonnay - blanco',2,'[{\"changed\": {\"fields\": [\"Nombre\", \"Descripcion\"]}}]',14,2),(32,'2025-02-16 21:35:58.097125','1','Factura 123 - Cliente: MMRE - Pagada',2,'[{\"changed\": {\"fields\": [\"Pagado\", \"Fecha pago\"]}}]',7,2),(33,'2025-02-16 22:47:24.360540','1','Factura 123 - Cliente: MMRE - Pagada',2,'[{\"added\": {\"name\": \"detalle factura\", \"object\": \"2 x Incognito (Valle Gpe) - 123\"}}]',7,2),(34,'2025-02-16 22:48:54.397189','1','Factura 123 - Cliente: MMRE - Pagada',2,'[{\"deleted\": {\"name\": \"detalle factura\", \"object\": \"5 x Incognito (Valle Gpe) - 123\"}}]',7,2),(35,'2025-02-16 22:50:48.574761','1','Factura 123 - Cliente: MMRE - Pagada',2,'[{\"changed\": {\"name\": \"detalle factura\", \"object\": \"3 x Anecdota SB - 123\", \"fields\": [\"Cantidad\"]}}]',7,2),(36,'2025-02-17 04:30:36.075454','2','Factura TEST001 - Cliente: Cliente de Prueba - Pagada',2,'[{\"added\": {\"name\": \"detalle factura\", \"object\": \"1 x Anecdota Primeros Pasos (4 meses) - TEST001\"}}]',7,2),(37,'2025-02-17 04:36:53.711782','1','Factura 123 - Cliente: MMRE - Pagada',2,'[{\"deleted\": {\"name\": \"detalle factura\", \"object\": \"3 x Anecdota SB - 123\"}}]',7,2),(38,'2025-02-17 04:38:56.081008','1','Factura 123 - Cliente: MMRE - Pagada',2,'[{\"added\": {\"name\": \"detalle factura\", \"object\": \"6 x Anecdota Primeros Pasos (4 meses) - 123\"}}]',7,2),(39,'2025-02-17 04:39:23.143595','2','Factura TEST001 - Cliente: Cliente de Prueba - Pagada',2,'[{\"changed\": {\"name\": \"detalle factura\", \"object\": \"6 x Anecdota Primeros Pasos (4 meses) - TEST001\", \"fields\": [\"Cantidad\"]}}]',7,2),(40,'2025-02-17 04:41:20.705585','2','Factura TEST001 - Cliente: Cliente de Prueba - Pagada',2,'[{\"added\": {\"name\": \"detalle factura\", \"object\": \"6 x Anecdota Chardonnay Chenin Blanc - TEST001\"}}]',7,2),(41,'2025-02-24 04:33:47.164539','349','Crabster Chardonnay - blanco',1,'[{\"added\": {}}]',14,2),(42,'2025-02-24 04:35:43.142713','2','Factura TEST001 - Cliente: Cliente de Prueba - Pagada',2,'[{\"added\": {\"name\": \"detalle factura\", \"object\": \"6 x Crabster Chardonnay - TEST001\"}}]',7,2);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(8,'compras','compra'),(11,'compras','compraproducto'),(9,'compras','empresa'),(12,'compras','producto'),(10,'compras','proveedor'),(5,'contenttypes','contenttype'),(13,'inventario','inventario'),(14,'inventario','producto'),(6,'sessions','session'),(16,'ventas','detallefactura'),(7,'ventas','factura'),(15,'ventas','pagofactura');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2024-10-30 01:39:10.005368'),(2,'auth','0001_initial','2024-10-30 01:39:10.643709'),(3,'admin','0001_initial','2024-10-30 01:39:10.853064'),(4,'admin','0002_logentry_remove_auto_add','2024-10-30 01:39:10.861040'),(5,'admin','0003_logentry_add_action_flag_choices','2024-10-30 01:39:10.871015'),(6,'contenttypes','0002_remove_content_type_name','2024-10-30 01:39:10.955073'),(7,'auth','0002_alter_permission_name_max_length','2024-10-30 01:39:11.039190'),(8,'auth','0003_alter_user_email_max_length','2024-10-30 01:39:11.063751'),(9,'auth','0004_alter_user_username_opts','2024-10-30 01:39:11.071719'),(10,'auth','0005_alter_user_last_login_null','2024-10-30 01:39:11.140057'),(11,'auth','0006_require_contenttypes_0002','2024-10-30 01:39:11.142521'),(12,'auth','0007_alter_validators_add_error_messages','2024-10-30 01:39:11.151336'),(13,'auth','0008_alter_user_username_max_length','2024-10-30 01:39:11.222075'),(14,'auth','0009_alter_user_last_name_max_length','2024-10-30 01:39:11.288674'),(15,'auth','0010_alter_group_name_max_length','2024-10-30 01:39:11.311107'),(16,'auth','0011_update_proxy_permissions','2024-10-30 01:39:11.319085'),(17,'auth','0012_alter_user_first_name_max_length','2024-10-30 01:39:11.386229'),(18,'sessions','0001_initial','2024-10-30 01:39:11.426109'),(19,'ventas','0001_initial','2024-10-31 05:45:11.976464'),(21,'compras','0002_empresa_remove_compra_emisora_remove_compra_mes_and_more','2024-11-02 01:56:37.397544'),(22,'compras','0003_proveedor_remove_compra_empresa_compra_proveedor_and_more','2024-11-02 02:34:08.046069'),(23,'compras','0001_initial','2024-11-02 02:49:30.867207'),(24,'compras','0002_producto_compraproducto','2024-11-02 03:18:39.048889'),(25,'compras','0003_alter_producto_proveedor','2024-11-05 04:42:31.527458'),(26,'inventario','0001_initial','2024-11-05 04:42:31.746073'),(27,'inventario','0002_remove_producto_precio_unitario_and_more','2025-02-04 05:12:18.140152'),(28,'inventario','0003_inventario_fecha_ingreso_inventario_stock_minimo_and_more','2025-02-04 05:26:21.845475'),(29,'ventas','0002_detallefactura_pagofactura','2025-02-09 06:31:11.802453'),(30,'ventas','0003_remove_detallefactura_subtotal_and_more','2025-02-16 21:23:43.672973'),(31,'ventas','0004_detallefactura_subtotal_and_more','2025-02-16 21:23:43.815976'),(32,'ventas','0005_detallefactura_precio_compra','2025-02-16 23:12:04.692095'),(33,'inventario','0004_producto_es_personalizado','2025-02-24 03:58:13.828178'),(34,'inventario','0005_producto_stock','2025-02-24 04:28:10.217009');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('h4xw1l7iyhe0i143gfk06nczdzluzhj1','.eJxVjEEOwiAURO_C2hDgU8p36b5nIJQPUjWQlHZlvLs06UJ3k5k3782c37fs9hZXtxC7MsUuv93swzOWY6CHL_fKQy3busz8QPi5Nj5Viq_byf4Jsm-5v2E0JkFIwgKlETBpSWoYEvVkdPcgyiDAgtUhCmURtdVGIWFEJOnZ5wvTQjdF:1tkH3V:lAE_eohr-kUm3tOtXhCDKqtAzF5TP7YuD7vBsD8qpFw','2025-03-04 06:26:05.965019'),('ii5ou243pbwwirllazaai43bc69ekpge','.eJxVjEEOwiAURO_C2hDgU8p36b5nIJQPUjWQlHZlvLs06UJ3k5k3782c37fs9hZXtxC7MsUuv93swzOWY6CHL_fKQy3busz8QPi5Nj5Viq_byf4Jsm-5v2E0JkFIwgKlETBpSWoYEvVkdPcgyiDAgtUhCmURtdVGIWFEJOnZ5wvTQjdF:1tfAsl:AV42hfPsR7qZoLfVFNMSdFQK8VdAncBAiKHPEfaBFe4','2025-02-18 04:49:55.346615'),('n2r48kmartk2wnc0oougmfp3l76gvosp','.eJxVjEEOwiAURO_C2hDgU8p36b5nIJQPUjWQlHZlvLs06UJ3k5k3782c37fs9hZXtxC7MsUuv93swzOWY6CHL_fKQy3busz8QPi5Nj5Viq_byf4Jsm-5v2E0JkFIwgKlETBpSWoYEvVkdPcgyiDAgtUhCmURtdVGIWFEJOnZ5wvTQjdF:1t6OLP:BF6k6ZJEhGvDWTNruAh0JqmKbTJNMpRm6U0udsH0CHk','2024-11-14 06:07:43.561939');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventario_inventario`
--

DROP TABLE IF EXISTS `inventario_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventario_inventario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cantidad` int NOT NULL,
  `fecha_actualizacion` datetime(6) NOT NULL,
  `producto_id` bigint NOT NULL,
  `fecha_ingreso` datetime(6) DEFAULT NULL,
  `stock_minimo` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `inventario_inventari_producto_id_f9e2c17a_fk_inventari` (`producto_id`),
  CONSTRAINT `inventario_inventari_producto_id_f9e2c17a_fk_inventari` FOREIGN KEY (`producto_id`) REFERENCES `inventario_producto` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventario_inventario`
--

LOCK TABLES `inventario_inventario` WRITE;
/*!40000 ALTER TABLE `inventario_inventario` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventario_inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventario_producto`
--

DROP TABLE IF EXISTS `inventario_producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventario_producto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` longtext,
  `proveedor_id` bigint NOT NULL,
  `precio_compra` decimal(10,2) NOT NULL,
  `precio_venta` decimal(10,2) NOT NULL,
  `tipo` varchar(50) DEFAULT NULL,
  `uva` varchar(100) DEFAULT NULL,
  `es_personalizado` tinyint(1) NOT NULL,
  `stock` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `inventario_producto_proveedor_id_2feee190_fk_compras_p` (`proveedor_id`),
  CONSTRAINT `inventario_producto_proveedor_id_2feee190_fk_compras_p` FOREIGN KEY (`proveedor_id`) REFERENCES `compras_proveedor` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=350 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventario_producto`
--

LOCK TABLES `inventario_producto` WRITE;
/*!40000 ALTER TABLE `inventario_producto` DISABLE KEYS */;
INSERT INTO `inventario_producto` VALUES (1,'Anecdota SB','',2,204.00,295.00,NULL,'Sauvignon Blanc',0,0),(2,'Anecdota Chardonnay Chenin Blanc','',2,204.00,295.00,NULL,'Chardonnay Chenin Blanc',0,0),(3,'Verdades (Valle Sto. Tomas)','',3,167.00,269.00,'Tinto','Cabernet Sauvignon',0,0),(4,'Anecdota CM','',2,162.00,289.00,NULL,'Cabernet Merlot',0,0),(5,'Anecdota Blend (Santo Tomas)','',2,204.00,315.00,NULL,'Tempranillo,Merlot,Cabernet S',0,0),(6,'Anecdota Primeros Pasos (4 meses)','',2,162.00,289.00,NULL,'Cabernet Merlot',0,0),(7,'Altotinto Chardonnay','Vino blanco mexicano con 9 meses en barrica',2,259.00,388.00,'blanco','Chardonnay',0,0),(8,'Altotinto Seleccion (Medalla Oro CB)','',2,274.00,420.00,NULL,'Cabernet,Nebbiolo,Petit Verdot',0,0),(9,'Altotinto (Valle Sto Tomas 15 meses)','',2,349.00,540.00,NULL,'Nebbiolo',0,0),(11,'Altotinto Gran Cabernet (18 meses)','',2,424.00,650.00,NULL,'Cabernet Sauvignon',0,0),(12,'Altotinto Alta Reserva (20 meses)','',2,625.00,790.00,NULL,'Cab Sauv,Temp,Nebbiolo,Merlot,Syrah',0,0),(65,'Altotinto Elite Albarino','',2,925.00,1.00,NULL,'Albarino',0,0),(66,'Altotinto Elite Nebbiolo (22 meses)','',2,925.00,1300.00,'tinto','Nebbiolo',0,0),(67,'Altotinto Elite Tannat (22 meses)','',2,925.00,1300.00,NULL,'Tannat',0,0),(68,'Altotinto Elite Malbec (22 meses)','',2,925.00,1300.00,NULL,'Malbec',0,0),(69,'Altotinto Elite Blend 10 uvas (22 ms)','',2,925.00,1300.00,NULL,'Nebbiolo Tannat Malbec CS Syrah',0,0),(70,'Alto Tinto Cosecha Tardia 500 ml','',2,325.00,449.00,NULL,'Petite Syrah',0,0),(71,'Datum Quinta Monasterio (Valle Gpe.)','',1,473.00,595.00,'Tinto','Merlot  Syrah  Nebbiolo',0,0),(72,'Incognito (Valle Gpe)','',1,392.00,520.00,'Tinto','Cabernet zinfandel Grenache',0,0),(73,'Santo Tomas SB','',1,304.00,395.00,'Blanco','Sauvignon Blanc',0,0),(74,'Santo Tomas Ch','',1,304.00,395.00,'Blanco','Chardonnay',0,0),(75,'Santo Tomas V','',1,304.00,395.00,'Blanco','Viogner',0,0),(76,'Santo Tomas GR','',1,359.00,448.00,'Rosado','Grenache',0,0),(77,'Santo Tomas Merlot','',1,398.00,487.00,'Tinto','Merlot',0,0),(78,'Santo Tomas Syrah','',1,398.00,487.00,'Tinto','Syrah',0,0),(79,'Tinta Mexico Santo Tomas','',1,406.00,495.00,'Tinto','Barbera Merlot',0,0),(80,'Blanco Mexico Santo Tomas','',1,315.00,462.00,'Blanco','Viogner',0,0),(81,'Unico Santo Tomas G Rva','',1,1720.00,1.00,'Tinto','Cabernet Merlot',0,0),(82,'Duetto Santo Tomas','',1,1720.00,1.00,'Tinto','Tempranillo Cabernet Sauvignon',0,0),(83,'202 Uvas (Ags Montenegro)','',5,375.00,450.00,'Tinto','Tempranillo Syrah  Malbec',0,0),(84,'Casa Silva Coleccion','',6,179.00,279.00,'Blanco','Chardonnay',0,0),(88,'Finca Andina','',6,101.00,225.00,'Tinto','Merlot',0,0),(90,'Toro De Piedra Gran Reserva','',3,303.00,450.00,'Tinto','Carmenere Cabernet Sauvignon',0,0),(92,'Oladia','',3,125.00,190.00,'Rosado','White Zinfandel',0,0),(93,'Reserva Familiar Montes Toscanini','',4,195.00,299.00,'Blanco','Sauvignon Blanc',0,0),(96,'Elegido  Bivarietal','',2,168.00,299.00,'tinto','Tannat Merlot',0,0),(97,'Elegido Reserva Montes Toscanini','',2,222.00,365.00,NULL,'Tannat Cabernet Sauvignon Merlot',0,0),(98,'Carlos Montes Criado En Roble 12M','',2,327.00,445.00,NULL,'Merlot',0,0),(101,'MT Criado en Roble 15 meses','',2,445.00,580.00,NULL,'Tannat',0,0),(102,'Corte Supremo Premium 18 meses','',2,619.00,799.00,NULL,'Cabernet Tannat Merlot',0,0),(103,'Crudo Barricado Montes T. 8 meses','',2,619.00,799.00,NULL,'Merlot  Tannat  cabernet Franc Syrah',0,0),(104,'Elsa Bianchi','',1,176.00,299.00,'Blanco','Torrontes',0,0),(105,'Carelli 34','',3,171.00,310.00,'Blanco','Torrontes',0,0),(109,'Carelli Madero Rva','',3,210.00,350.00,'Tinto','Cabernet Franc',0,0),(111,'Carla Chiaro Reserva','',3,291.00,440.00,'Tinto','Bonarda',0,0),(113,'Carla Fino Organico','',3,175.00,299.00,'Tinto','Cabernet sauvignon',0,0),(115,'Pequena Vasija','',1,188.00,299.00,'Tinto','Syrah-Malbec',0,0),(117,'Ramon Roqueta Tina 16 Joven (Catalun','',1,162.00,299.00,'Tinto','Tempranillo',0,0),(118,'Ramon Roqueta Crianza (Cataluna)','',1,180.00,315.00,'Tinto','Tempranillo',0,0),(119,'Vinder','',7,92.00,169.00,'Blanco','Chardonnay',0,0),(123,'12 Lunas (Somontano)','',3,264.00,395.00,'Tinto','Tempranillo Syrah Garnacha Cabernet S',0,0),(124,'12 lunas Char/Gewurz (Somontano)','',3,267.00,395.00,'Blanco','Chardonnay Gewurztraminer',0,0),(125,'Laus Chardonnay (Somontano)','',1,284.00,385.00,'Blanco','Chardonnay',0,0),(126,'Laus Joven (Somontano)','',1,185.00,295.00,'Tinto','Merlot Syrah',0,0),(128,'Senorio Villarica Juanito Rias Baixas','',3,403.00,550.00,'Blanco','Albarino',0,0),(129,'Rias del Mar Rias Baixas','',1,395.00,510.00,'Blanco','Albarino',0,0),(130,'Valserrano (Rioja)','',3,383.00,495.00,'Tinto','Tempranillo Mazuelo',0,0),(131,'Monteabellon 5 meses (R  Duero)','',3,246.00,379.00,'Tinto','Tempranillo',0,0),(132,'Protos Verdejo','',8,287.00,399.00,'Blanco','Verdejo',0,0),(133,'Protos Clarete','',8,282.00,385.00,'Rosado','Tempranillo Merlot Syrah',0,0),(134,'Protos 9 meses (Organico)','',8,382.00,470.00,'Tinto','Tinta del Pais',0,0),(135,'Aire de Protos  (Cigales)','',8,344.00,419.00,'Rosado','Garnacha  Albillo  Verdejo  Viura  Sauvignon',0,0),(136,'Protos Crianza (Ribera del Duero)','',8,633.00,730.00,'Tinto','Tinta del Pais',0,0),(137,'Protos Reserva (Ribera del Duero)','',8,1030.00,1290.00,'tinto','Tinta del Pais',0,0),(138,'Rocca Lupo Nero Bianco( Sicilia IGT)','',4,99.00,195.00,'Blanco','Catarratto Grecanico Inzolia',0,0),(139,'Rocca Lupo Nero (Puglia IGT)','',4,99.00,195.00,'Tinto','Sangiovese',0,0),(140,'Rocca Montepulciano d\'Abruzzo','',4,173.00,276.00,'Tinto','Montepulciano',0,0),(141,'Rocca Pinot Grigio Rossato (Pavia IGT)','',4,216.00,299.00,'Rosado','Pinot Grigio',0,0),(142,'Rocca Pinot Grigio (Venezie IGT)','',4,220.00,315.00,'Blanco','Pinot Grigio',0,0),(143,'Rocca 5 Vite','',4,294.00,399.00,'Tinto','N. Amaro N. de Troia Malvasia prmtvo S',0,0),(144,'Rocca Dolcetto Sacc (Piemonte DOC','',4,234.00,332.00,'Tinto','Dolcetto',0,0),(145,'Rocca Perciata (Sicilia IGT)','',4,207.00,310.00,'Blanco','Insolia Chardonnay',0,0),(147,'Firriato Della Corte (Sicilia IGT)','',4,360.00,470.00,'Tinto','Nero Davola',0,0),(148,'firriato Caeles  (Sicilia IGT)','',4,355.00,449.00,'Tinto','Syrah',0,0),(149,'Altavilla Della Corte (Sicilia IGT)','',4,342.00,450.00,'Tinto','Cabernet Sauvginon',0,0),(150,'Ilivia Leone de Castris (Puglia IGT)','',4,277.00,390.00,'Tinto','Primitivo',0,0),(151,'Illivia Leone de Castris(Salento IGT)','',4,260.00,355.00,'Tinto','Negroamaro',0,0),(152,'Villa Santera (Puglia DOC)','',4,525.00,640.00,'Tinto','Primitivo Di Manduria',0,0),(153,'Colpo Di Zappa Leone Di Castris','',4,838.00,1.00,'Tinto','Primitivo Di Giogia',0,0),(154,'Perlui Leone Di Castris (Puglia DOC)','',4,1234.00,1.00,'Tinto','Primitivo',0,0),(155,'Scaia Bianco(Trevenezie IGT)','',4,355.00,459.00,'Blanco','Garganera Chardonnay',0,0),(156,'Scaia Rosso (Venetto IGT)','',4,355.00,459.00,'Tinto','Corvina',0,0),(157,'Il Lemos Leone de Castris','',4,399.00,420.00,'Tinto','Sussumaniello',0,0),(158,'Dika Grasevina Feravino','',9,475.00,595.00,'Blanco','Grasevina',0,0),(160,'Rajnski Rizling Orahovica','',9,444.00,585.00,'Blanco','Rizling',0,0),(161,'Dika Zweigelt 2017','',9,494.00,650.00,'Tinto','Lovrijenac /Frankovka',0,0),(162,'Dika Frankovka','',9,494.00,650.00,'Tinto','frankovka',0,0),(163,'Dika Cabernet Franc','',9,494.00,650.00,'Tinto','Cabernet Franc',0,0),(164,'Peljesac 2019','',9,384.00,585.00,'Tinto','Plavac Mali',0,0),(165,'Mediterano  2013','',9,765.00,885.00,'Tinto','Plavac  Mali',0,0),(166,'Ivan Dolac Ecologico Organico 2010','',9,860.00,1.00,'Tinto','Plavac Mali',0,0),(167,'Dingac 50','',9,1012.00,1.00,'Tinto','Plavac Mali',0,0),(168,'Fleur de Rose Georges Duboeuf','',10,266.00,385.00,'Rosado','Pinot Noir',0,0),(169,'Ch Bourbon La Chapelle (Medoc)','',10,347.00,455.00,'Tinto','Cabernet Sauvignon  Merlot',0,0),(170,'Chateau Castera (Medoc)','',10,539.00,670.00,'Ttinto','Cabernet Sauvignon  Cabernet Franc',0,0),(171,'Cotes Du Rone Fam Perrin','',10,329.00,440.00,'Tinto','Syrah Grenache  Murvedre',0,0),(172,'Uby N2 (por Llegar)','',10,312.00,410.00,'Blanco','Ugny Blanc Colombard',0,0),(173,'Uby N3 (Por Llegar)','',10,272.00,380.00,'Blanco','Colombard Sauvignon Blanc',0,0),(174,'Uby N4 (Por Llegar)','',10,312.00,410.00,'Blanco','Gros Petit Manseng',0,0),(175,'Uby N6 Rose','',10,304.00,395.00,'Rosado','Cabernet Sauvignon Franc Merlot',0,0),(176,'Uby N7','',10,312.00,410.00,'Tinto','Merlot Tannat',0,0),(177,'Moulin de Gassac (Por Llegar)','',10,315.00,410.00,'Tinto','Pinot Noir',0,0),(178,'Moulin de Gassac','',10,315.00,410.00,'Tinto','cabernet Sauvignon',0,0),(180,'Chateau Du Pouey','',10,352.00,450.00,'Tinto','Tannat Cabernet Franc Cab Sauv',0,0),(181,'Lapompadour Castelmaure','',10,408.00,510.00,'Tinto','Carignan Syrah Grenache',0,0),(182,'Flying Solo','',5,275.00,390.00,'Tinto','Grenache  Syrah',0,0),(183,'Flaying Solo Rose','',5,275.00,370.00,'Rosado','Grenache & Syrah',0,0),(184,'Pluma Vinho Verde','',8,231.00,345.00,'Blanco','Avesso Loureiro Trajadura Arinto',0,0),(185,'Conserva vinho Verde','',8,145.00,227.00,'Blanco','ArintoArinto',0,0),(186,'Conserva Rosado','',8,145.00,227.00,'Rosado','Vinhao Borracal Espadeiro',0,0),(187,'Coastal Estate Chaardonnay','',1,234.00,328.00,'Blanco','Chardonnay',0,0),(188,'Coastal Estate cabenet sauvignon','',1,234.00,335.00,'Tinto','Cabernet sauvignon',0,0),(189,'coastal estate Pinot Noir','',1,234.00,335.00,'Tinto','Pinot Noir',0,0),(190,'Lambrusco Antiche Tradizioni (ER)','',4,146.00,210.00,'Tinto Espumoso','Salamino Maestri Marani Ancellosa',0,0),(191,'Dueto Spumante Tenuta San Giorgio','',4,186.00,295.00,'Espumoso','Pinot Blanca Chardonnay',0,0),(192,'Flumen Prosecco Tenuta Sn Giorgio Ext','',4,277.00,390.00,'Espumoso','Glera',0,0),(193,'Gaudensius Blanc deNoir','',4,759.00,899.00,'Espumoso','Nerello Mascalese',0,0),(194,'Dezzani Asti Spumante (Piemonte)','',4,277.00,379.00,'Espumoso','Moscato',0,0),(195,'Cava +&+ Brut (Esp)','',8,256.00,350.00,'Espumoso','Chardonnay  Xare-lo  Parellada',0,0),(196,'Louis Perdrier Brut (Fra)','',1,228.00,325.00,'Espumoso','Chardonnay  Pinot Noir  Pinot Blanc',0,0),(197,'Cossy 1er cru','',4,842.00,1.00,'Champagne','Chardonnay  Pinot Noir  Meunier',0,0),(198,'Vermouth Tinto Poli','',4,525.00,790.00,'Destilado','Merlot y 33 Botanicos',0,0),(199,'Grappa Sarpa Poli','',4,530.00,795.00,'Destilado','Merlot / Cabernet',0,0),(200,'Ginebra Marconi 46 Poli','',4,995.00,1.00,'Destilado','Bayas enebro moscatel pino nero menta',0,0),(217,'Altotinto Elite Blend 10 uvas (22 ms)','',2,925.00,1300.00,'tinto','Nebbiolo Tannat Malbec CS Syrah',0,0),(270,'Viceversa Roble (Navarra)','',3,161.00,299.00,'tinto','Cabernet Merlot Tempranillo',0,0),(275,'Laus Barrica (Somontano)','',1,297.00,399.00,'tinto','Merlot  Cabernet Sauvignon  Syrah',0,0),(349,'Crabster Chardonnay','Crabster Chardonnay Personalizado',2,162.00,289.00,'blanco','Chardonnay',1,36);
/*!40000 ALTER TABLE `inventario_producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas_detallefactura`
--

DROP TABLE IF EXISTS `ventas_detallefactura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas_detallefactura` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `factura_id` bigint NOT NULL,
  `producto_id` bigint NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `precio_compra` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ventas_detallefactura_factura_id_5804bb5e_fk_ventas_factura_id` (`factura_id`),
  KEY `ventas_detallefactur_producto_id_4456d52e_fk_inventari` (`producto_id`),
  CONSTRAINT `ventas_detallefactur_producto_id_4456d52e_fk_inventari` FOREIGN KEY (`producto_id`) REFERENCES `inventario_producto` (`id`),
  CONSTRAINT `ventas_detallefactura_factura_id_5804bb5e_fk_ventas_factura_id` FOREIGN KEY (`factura_id`) REFERENCES `ventas_factura` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas_detallefactura`
--

LOCK TABLES `ventas_detallefactura` WRITE;
/*!40000 ALTER TABLE `ventas_detallefactura` DISABLE KEYS */;
INSERT INTO `ventas_detallefactura` VALUES (3,6,289.00,2,6,1734.00,162.00),(4,6,250.00,1,6,1500.00,162.00),(5,6,318.00,2,2,1908.00,204.00),(6,6,289.00,2,349,1734.00,162.00);
/*!40000 ALTER TABLE `ventas_detallefactura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas_factura`
--

DROP TABLE IF EXISTS `ventas_factura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas_factura` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `folio_factura` varchar(20) NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `cliente` varchar(100) NOT NULL,
  `fecha_facturacion` date NOT NULL,
  `vencimiento` date DEFAULT NULL,
  `pagado` tinyint(1) NOT NULL,
  `fecha_pago` date DEFAULT NULL,
  `notas` longtext,
  PRIMARY KEY (`id`),
  UNIQUE KEY `folio_factura` (`folio_factura`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas_factura`
--

LOCK TABLES `ventas_factura` WRITE;
/*!40000 ALTER TABLE `ventas_factura` DISABLE KEYS */;
INSERT INTO `ventas_factura` VALUES (1,'123',1500.00,'MMRE','2024-10-31','2024-11-13',1,'2025-02-16','https://mail.google.com/mail/u/0/?tab=rm&ogbl#inbox/FMfcgzQXJsvTPtxrXgMJgPwgKvLxqgKp'),(2,'TEST001',5376.00,'Cliente de Prueba','2025-02-10','2025-02-25',1,'2025-02-15','');
/*!40000 ALTER TABLE `ventas_factura` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas_pagofactura`
--

DROP TABLE IF EXISTS `ventas_pagofactura`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas_pagofactura` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha_pago` date NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `factura_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ventas_pagofactura_factura_id_0e261358_fk_ventas_factura_id` (`factura_id`),
  CONSTRAINT `ventas_pagofactura_factura_id_0e261358_fk_ventas_factura_id` FOREIGN KEY (`factura_id`) REFERENCES `ventas_factura` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas_pagofactura`
--

LOCK TABLES `ventas_pagofactura` WRITE;
/*!40000 ALTER TABLE `ventas_pagofactura` DISABLE KEYS */;
/*!40000 ALTER TABLE `ventas_pagofactura` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-03-07  1:10:29
