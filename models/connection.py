import mysql.connector
import os
import pandas as pd
import dotenv

dotenv.load_dotenv(dotenv.find_dotenv()) 

def connect_db():
  connection = mysql.connector.connect (
    host = os.getenv("host"),
    port = os.getenv("port"),
    user = os.getenv("user"),
    password = os.getenv("password"),
    database = os.getenv("database"),
  )
  return connection

def get_customer_spend_month(connection,cod_uno):
  cursor = connection.cursor()
  comando = (f''' SELECT vp.cod_pedido as COD_PEDIDO, vp.dt_aprovacao as DT_APROVACAO, vp.vl_total_pedido as VL_TOTAL_PEDIDO
                  FROM vd_pedido as vp 
                  JOIN cd_cliente as cc 
                  on cc.cod_cliente = vp.cod_cliente 
                  WHERE dt_entrega_original BETWEEN CURDATE() - INTERVAL (DAY(CURDATE())-1) DAY AND CURDATE() 
                  and cc.cod_cliente = {cod_uno}
                  and vp.situacao < 100;
                  ''')
  cursor.execute(comando)
  result = cursor.fetchall()
  cursor.close()
  connection.close()
  return result

def return_customer_spend_month(cod_uno):
  value = get_customer_spend_month(connect_db(), cod_uno)
  dataFrame = pd.DataFrame(value, columns=['ID', 'DATA', 'VALOR'])
  dataFrame = dataFrame.append({'ID': 'Total', 'DATA': '', 'VALOR': dataFrame['VALOR'].sum()}, ignore_index=True)
  return dataFrame