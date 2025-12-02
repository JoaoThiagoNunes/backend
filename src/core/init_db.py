from src.core.database import engine
from src.modules.shared.base import Base
from src.modules.features.uploads import Upload
from src.modules.features.escolas import Escola
from src.modules.features.calculos import CalculosProfin

def init_database():
    """Inicializa o banco de dados criando todas as tabelas"""
    print("Iniciando criação das tabelas...")
    
    try:
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        print("✓ Tabelas criadas com sucesso!")
        print("\nTabelas criadas:")
        print("  - uploads")
        print("  - escolas")
        print("  - calculos_profin")
        
    except Exception as e:
        print(f"✗ Erro ao criar tabelas: {e}")
        raise

def drop_all_tables():
    """Remove todas as tabelas (use com cuidado!)"""
    print("⚠️  ATENÇÃO: Removendo todas as tabelas...")
    response = input("Tem certeza? Digite 'SIM' para confirmar: ")
    
    if response == "SIM":
        try:
            Base.metadata.drop_all(bind=engine)
            print("✓ Todas as tabelas foram removidas!")
        except Exception as e:
            print(f"✗ Erro ao remover tabelas: {e}")
            raise
    else:
        print("Operação cancelada.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_all_tables()
    
    init_database()