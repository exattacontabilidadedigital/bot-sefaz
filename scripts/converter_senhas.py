#!/usr/bin/env python3
"""
Script para converter senhas criptografadas para texto plano
"""
import sqlite3
from cryptography.fernet import Fernet

def converter_senhas():
    """Converte todas as senhas do banco de criptografadas para texto plano"""
    
    print("🔄 Convertendo senhas de criptografadas para texto plano...")
    print("=" * 60)
    
    # Carregar chave antiga para descriptografar
    try:
        with open("encryption_key.txt", 'rb') as f:
            key = f.read()
        cipher = Fernet(key)
        print("✅ Chave de criptografia carregada")
    except Exception as e:
        print(f"❌ Erro ao carregar chave: {e}")
        return
    
    # Conectar ao banco
    conn = sqlite3.connect("sefaz_consulta.db")
    cursor = conn.cursor()
    
    try:
        # Buscar todas as empresas
        cursor.execute("SELECT id, nome_empresa, senha FROM empresas")
        empresas = cursor.fetchall()
        
        print(f"📊 Encontradas {len(empresas)} empresas para converter\n")
        
        for empresa in empresas:
            emp_id, nome, senha_criptografada = empresa
            
            print(f"🏢 Convertendo: {nome}")
            
            try:
                # Tentar descriptografar a senha
                senha_texto_plano = cipher.decrypt(senha_criptografada.encode()).decode()
                
                # Atualizar no banco com texto plano
                cursor.execute("UPDATE empresas SET senha = ? WHERE id = ?", 
                             (senha_texto_plano, emp_id))
                
                print(f"   ✅ Convertida: {senha_criptografada[:20]}... → {senha_texto_plano}")
                
            except Exception as e:
                print(f"   ⚠️  Já em texto plano ou erro: {e}")
                # Se der erro, assume que já está em texto plano
                print(f"   📝 Mantendo como está: {senha_criptografada}")
        
        # Confirmar mudanças
        conn.commit()
        print(f"\n✅ Conversão concluída! {len(empresas)} empresas processadas")
        
        # Verificar resultado
        print("\n📋 Verificando senhas convertidas:")
        cursor.execute("SELECT id, nome_empresa, senha FROM empresas")
        empresas_verificacao = cursor.fetchall()
        
        for empresa in empresas_verificacao:
            emp_id, nome, senha = empresa
            print(f"   {emp_id}: {nome} → Senha: {senha}")
        
    except Exception as e:
        print(f"❌ Erro durante conversão: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    converter_senhas()