"""
Testes para rotas de complemento
"""
import pytest
from fastapi import status
from datetime import datetime


class TestUploadComplemento:
    """Testes para POST /complemento/upload"""
    
    def test_upload_complemento_success(self, client, sample_ano_letivo, sample_upload, sample_excel_file):
        """Testa upload bem-sucedido de planilha de complemento"""
        response = client.post(
            "/complemento/upload",
            files={"file": ("complemento.xlsx", sample_excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            params={"ano_letivo_id": sample_ano_letivo.id, "upload_base_id": sample_upload.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "complemento_upload_id" in data
        assert data["ano_letivo_id"] == sample_ano_letivo.id
        assert "total_escolas_processadas" in data
    
    def test_upload_complemento_invalid_file_type(self, client):
        """Testa upload com tipo de arquivo inválido"""
        response = client.post(
            "/complemento/upload",
            files={"file": ("test.txt", b"invalid content", "text/plain")}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Arquivo deve ser Excel" in response.json()["detail"]
    
    def test_upload_complemento_missing_file(self, client):
        """Testa upload sem arquivo"""
        response = client.post("/complemento/upload")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestObterComplementosAgrupados:
    """Testes para GET /complemento/repasse"""
    
    def test_obter_complementos_agrupados_success(self, client, sample_ano_letivo, sample_complemento_upload, 
                                                   sample_complemento_escolas, sample_liberacao):
        """Testa obtenção de resumo agrupado por folhas"""
        response = client.get(
            "/complemento/repasse",
            params={"ano_letivo_id": sample_ano_letivo.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "total_folhas" in data
        assert "total_escolas" in data
        assert "valor_total_reais" in data
        assert "folhas" in data
        assert isinstance(data["folhas"], list)
    
    def test_obter_complementos_agrupados_with_upload_id(self, client, sample_complemento_upload, 
                                                         sample_complemento_escolas):
        """Testa obtenção com complemento_upload_id específico"""
        response = client.get(
            "/complemento/repasse",
            params={"complemento_upload_id": sample_complemento_upload.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestObterComplementoDetalhado:
    """Testes para GET /complemento/{complemento_upload_id}"""
    
    def test_obter_complemento_detalhado_success(self, client, sample_complemento_upload, 
                                                  sample_complemento_escolas):
        """Testa obtenção de detalhes de um upload"""
        response = client.get(f"/complemento/{sample_complemento_upload.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["complemento_upload_id"] == sample_complemento_upload.id
        assert "escolas" in data
        assert isinstance(data["escolas"], list)
        assert len(data["escolas"]) == 2
    
    def test_obter_complemento_detalhado_not_found(self, client):
        """Testa obtenção de upload inexistente"""
        response = client.get("/complemento/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "não encontrado" in response.json()["detail"].lower()


class TestObterComplementosEscola:
    """Testes para GET /complemento/escola/{escola_id}"""
    
    def test_obter_complementos_escola_success(self, client, sample_escolas, sample_complemento_escolas):
        """Testa obtenção de histórico de complementos de uma escola"""
        response = client.get(f"/complemento/escola/{sample_escolas[0].id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["escola_id"] == sample_escolas[0].id
        assert "complementos" in data
        assert isinstance(data["complementos"], list)
    
    def test_obter_complementos_escola_not_found(self, client):
        """Testa obtenção de escola inexistente"""
        response = client.get("/complemento/escola/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "não encontrada" in response.json()["detail"].lower()


class TestListarComplementos:
    """Testes para GET /complemento/"""
    
    def test_listar_complementos_success(self, client, sample_complemento_upload):
        """Testa listagem de uploads de complemento"""
        response = client.get("/complemento/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_listar_complementos_with_filters(self, client, sample_ano_letivo, sample_complemento_upload):
        """Testa listagem com filtros"""
        response = client.get(
            "/complemento/",
            params={"ano_letivo_id": sample_ano_letivo.id, "page": 1, "page_size": 10}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestLiberarEscolasComplemento:
    """Testes para POST /complemento/liberar"""
    
    def test_liberar_escolas_complemento_success(self, client, sample_escolas, sample_complemento_upload):
        """Testa liberação de escolas para uma folha"""
        response = client.post(
            "/complemento/liberar",
            json={
                "escola_ids": [sample_escolas[0].id],
                "numero_folha": 1,
                "complemento_upload_id": sample_complemento_upload.id
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["numero_folha"] == 1
        assert "liberacoes" in data
        assert len(data["liberacoes"]) == 1
    
    def test_liberar_escolas_complemento_empty_list(self, client):
        """Testa liberação com lista vazia"""
        response = client.post(
            "/complemento/liberar",
            json={
                "escola_ids": [],
                "numero_folha": 1
            }
        )
        
        # Pode retornar 400 ou 200 dependendo da implementação
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK]
    
    def test_liberar_escolas_complemento_without_upload_id(self, client, sample_ano_letivo, 
                                                          sample_escolas, sample_complemento_upload):
        """Testa liberação sem especificar complemento_upload_id (deve usar o mais recente)"""
        response = client.post(
            "/complemento/liberar",
            json={
                "escola_ids": [sample_escolas[0].id],
                "numero_folha": 2,
                "ano_letivo_id": sample_ano_letivo.id
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestListarLiberacoesComplemento:
    """Testes para GET /complemento/liberacoes"""
    
    def test_listar_liberacoes_success(self, client, sample_ano_letivo, sample_liberacao):
        """Testa listagem de liberações"""
        response = client.get(
            "/complemento/liberacoes",
            params={"ano_letivo_id": sample_ano_letivo.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "liberacoes" in data
        assert isinstance(data["liberacoes"], list)
    
    def test_listar_liberacoes_with_filters(self, client, sample_ano_letivo, sample_complemento_upload, sample_liberacao):
        """Testa listagem com filtros"""
        response = client.get(
            "/complemento/liberacoes",
            params={
                "complemento_upload_id": sample_complemento_upload.id,
                "numero_folha": 1,
                "liberada": True,
                "ano_letivo_id": sample_ano_letivo.id
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
    
    def test_listar_liberacoes_by_escola(self, client, sample_ano_letivo, sample_escolas, sample_liberacao):
        """Testa listagem filtrada por escola"""
        response = client.get(
            "/complemento/liberacoes",
            params={
                "escola_id": sample_escolas[0].id,
                "ano_letivo_id": sample_ano_letivo.id
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


class TestAtualizarLiberacaoComplemento:
    """Testes para PUT /complemento/liberacoes/{liberacao_id}"""
    
    def test_atualizar_liberacao_success(self, client, sample_liberacao):
        """Testa atualização de liberação"""
        response = client.put(
            f"/complemento/liberacoes/{sample_liberacao.id}",
            json={
                "numero_folha": 2,
                "liberada": True
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["liberacao"]["numero_folha"] == 2
        assert data["liberacao"]["liberada"] is True
    
    def test_atualizar_liberacao_not_found(self, client):
        """Testa atualização de liberação inexistente"""
        response = client.put(
            "/complemento/liberacoes/99999",
            json={"numero_folha": 2}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "não encontrada" in response.json()["detail"].lower()
    
    def test_atualizar_liberacao_partial_update(self, client, sample_liberacao):
        """Testa atualização parcial de liberação"""
        response = client.put(
            f"/complemento/liberacoes/{sample_liberacao.id}",
            json={"liberada": False}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["liberacao"]["liberada"] is False
