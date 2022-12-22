import mysql.connector
from odoo import fields, models
import dotenv
import os

dotenv.load_dotenv(dotenv.find_dotenv()) 

def connection():
  conexao = mysql.connector.connect (
    host = os.getenv("host"),
    port = os.getenv("port"),
    user = os.getenv("user"),
    password = os.getenv("password"),
    database = os.getenv("database"),
  )
  return conexao

def query(conexao,cod_uno):
  cursor = conexao.cursor()
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
  conexao.close()
  return result