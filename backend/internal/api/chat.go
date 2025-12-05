package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/datamigrate-ai/backend/internal/config"
	"github.com/gin-gonic/gin"
)

// ChatHandler handles AI chat requests
type ChatHandler struct {
	cfg           *config.Config
	aiServiceURL  string
	httpClient    *http.Client
}

// ChatMessage represents a chat message
type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest represents the chat request body
type ChatRequest struct {
	Message  string        `json:"message"`
	History  []ChatMessage `json:"history,omitempty"`
	Language string        `json:"language,omitempty"` // Language code: en, da, es, pt, no, sv, de
}

// ChatResponse represents the chat response
type ChatResponse struct {
	Response string   `json:"response"`
	Sources  []string `json:"sources,omitempty"`
}

// NewChatHandler creates a new chat handler
func NewChatHandler(cfg *config.Config) *ChatHandler {
	aiServiceURL := os.Getenv("AI_SERVICE_URL")
	if aiServiceURL == "" {
		aiServiceURL = "http://localhost:8081"
	}

	return &ChatHandler{
		cfg:          cfg,
		aiServiceURL: aiServiceURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Chat handles chat messages by proxying to the AI service
// @Summary Send chat message
// @Description Send a message to the AI support assistant
// @Tags chat
// @Accept json
// @Produce json
// @Param request body ChatRequest true "Chat request"
// @Success 200 {object} ChatResponse
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Security BearerAuth
// @Router /chat [post]
func (h *ChatHandler) Chat(c *gin.Context) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	if req.Message == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Message is required"})
		return
	}

	// Try to proxy to AI service
	response, err := h.proxyToAIService(req)
	if err != nil {
		log.Printf("[Chat] AI service error, using fallback: %v", err)
		// Fallback to local knowledge base response
		response = h.getFallbackResponse(req.Message, req.Language)
	}

	c.JSON(http.StatusOK, response)
}

// proxyToAIService forwards the request to the Python AI service
func (h *ChatHandler) proxyToAIService(req ChatRequest) (*ChatResponse, error) {
	// Marshal request
	jsonBody, err := json.Marshal(req)
	if err != nil {
		log.Printf("[Chat] Failed to marshal request: %v", err)
		return nil, err
	}

	// Create request to AI service
	aiURL := h.aiServiceURL + "/chat"
	log.Printf("[Chat] Proxying to AI service: %s", aiURL)
	aiReq, err := http.NewRequest("POST", aiURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		log.Printf("[Chat] Failed to create request: %v", err)
		return nil, err
	}
	aiReq.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := h.httpClient.Do(aiReq)
	if err != nil {
		log.Printf("[Chat] Failed to call AI service: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("AI service returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		log.Printf("[Chat] Failed to parse AI response: %v", err)
		return nil, err
	}

	log.Printf("[Chat] AI service responded successfully")
	return &chatResp, nil
}

// getFallbackResponse returns a fallback response when AI service is unavailable
func (h *ChatHandler) getFallbackResponse(message string, language string) *ChatResponse {
	// Check for security-related keywords
	lowerMsg := message
	for i := 0; i < len(lowerMsg); i++ {
		if lowerMsg[i] >= 'A' && lowerMsg[i] <= 'Z' {
			lowerMsg = lowerMsg[:i] + string(lowerMsg[i]+32) + lowerMsg[i+1:]
		}
	}

	// Security responses
	if contains(lowerMsg, "segur") || contains(lowerMsg, "proteg") || contains(lowerMsg, "security") || contains(lowerMsg, "protect") || contains(lowerMsg, "sicher") || contains(lowerMsg, "sikker") {
		securityResponses := map[string]string{
			"en": `Your data is protected with enterprise-grade security:
- All data is encrypted in transit (TLS 1.3) and at rest (AES-256)
- Database credentials are encrypted and never stored in plain text
- JWT authentication with secure token management
- Role-based access control (RBAC)
- Audit logging of all operations
- No data is shared with third parties`,
			"es": `Tus datos están protegidos con seguridad de nivel empresarial:
- Todos los datos están cifrados en tránsito (TLS 1.3) y en reposo (AES-256)
- Las credenciales de base de datos están cifradas y nunca se almacenan en texto plano
- Autenticación JWT con gestión segura de tokens
- Control de acceso basado en roles (RBAC)
- Registro de auditoría de todas las operaciones
- No se comparten datos con terceros`,
			"da": `Dine data er beskyttet med sikkerhed på virksomhedsniveau:
- Alle data er krypteret under transport (TLS 1.3) og i hvile (AES-256)
- Database-legitimationsoplysninger er krypteret og gemmes aldrig i klartekst
- JWT-godkendelse med sikker token-håndtering
- Rollebaseret adgangskontrol (RBAC)
- Revisionslogning af alle operationer
- Ingen data deles med tredjeparter`,
			"de": `Ihre Daten sind mit Enterprise-Sicherheit geschützt:
- Alle Daten sind während der Übertragung (TLS 1.3) und im Ruhezustand (AES-256) verschlüsselt
- Datenbank-Anmeldedaten sind verschlüsselt und werden nie im Klartext gespeichert
- JWT-Authentifizierung mit sicherer Token-Verwaltung
- Rollenbasierte Zugriffskontrolle (RBAC)
- Audit-Protokollierung aller Operationen
- Keine Daten werden mit Dritten geteilt`,
			"pt": `Seus dados são protegidos com segurança de nível empresarial:
- Todos os dados são criptografados em trânsito (TLS 1.3) e em repouso (AES-256)
- Credenciais de banco de dados são criptografadas e nunca armazenadas em texto simples
- Autenticação JWT com gerenciamento seguro de tokens
- Controle de acesso baseado em funções (RBAC)
- Registro de auditoria de todas as operações
- Nenhum dado é compartilhado com terceiros`,
			"no": `Dataene dine er beskyttet med sikkerhet på bedriftsnivå:
- Alle data er kryptert under overføring (TLS 1.3) og i hvile (AES-256)
- Database-legitimasjon er kryptert og lagres aldri i klartekst
- JWT-autentisering med sikker token-håndtering
- Rollebasert tilgangskontroll (RBAC)
- Revisjonslogging av alle operasjoner
- Ingen data deles med tredjeparter`,
			"sv": `Dina data skyddas med säkerhet på företagsnivå:
- All data är krypterad under överföring (TLS 1.3) och i vila (AES-256)
- Databasuppgifter är krypterade och lagras aldrig i klartext
- JWT-autentisering med säker token-hantering
- Rollbaserad åtkomstkontroll (RBAC)
- Revisionsloggning av alla operationer
- Ingen data delas med tredje part`,
		}
		if resp, ok := securityResponses[language]; ok {
			return &ChatResponse{Response: resp}
		}
		return &ChatResponse{Response: securityResponses["en"]}
	}

	// Migration responses
	if contains(lowerMsg, "migra") || contains(lowerMsg, "crear") || contains(lowerMsg, "create") || contains(lowerMsg, "nuevo") || contains(lowerMsg, "new") {
		migrationResponses := map[string]string{
			"en": `To create a migration:
1. Go to Migrations > New Migration
2. Configure your MSSQL connection (host, database, credentials)
3. Select tables to migrate
4. Choose your target warehouse (Snowflake, BigQuery, Fabric, etc.)
5. Configure dbt project settings
6. Start the migration - AI will generate models, tests, and documentation`,
			"es": `Para crear una migración:
1. Ve a Migraciones > Nueva Migración
2. Configura tu conexión MSSQL (host, base de datos, credenciales)
3. Selecciona las tablas a migrar
4. Elige tu almacén de destino (Snowflake, BigQuery, Fabric, etc.)
5. Configura los ajustes del proyecto dbt
6. Inicia la migración - la IA generará modelos, tests y documentación`,
			"da": `For at oprette en migrering:
1. Gå til Migreringer > Ny Migrering
2. Konfigurer din MSSQL-forbindelse (host, database, legitimationsoplysninger)
3. Vælg tabeller til migrering
4. Vælg dit mål-warehouse (Snowflake, BigQuery, Fabric, osv.)
5. Konfigurer dbt-projektindstillinger
6. Start migreringen - AI genererer modeller, tests og dokumentation`,
			"de": `Um eine Migration zu erstellen:
1. Gehen Sie zu Migrationen > Neue Migration
2. Konfigurieren Sie Ihre MSSQL-Verbindung (Host, Datenbank, Anmeldedaten)
3. Wählen Sie zu migrierende Tabellen
4. Wählen Sie Ihr Ziel-Warehouse (Snowflake, BigQuery, Fabric, etc.)
5. Konfigurieren Sie dbt-Projekteinstellungen
6. Starten Sie die Migration - KI generiert Modelle, Tests und Dokumentation`,
			"pt": `Para criar uma migração:
1. Vá para Migrações > Nova Migração
2. Configure sua conexão MSSQL (host, banco de dados, credenciais)
3. Selecione as tabelas para migrar
4. Escolha seu warehouse de destino (Snowflake, BigQuery, Fabric, etc.)
5. Configure as configurações do projeto dbt
6. Inicie a migração - a IA gerará modelos, testes e documentação`,
			"no": `For å opprette en migrering:
1. Gå til Migreringer > Ny Migrering
2. Konfigurer MSSQL-tilkoblingen din (host, database, legitimasjon)
3. Velg tabeller for migrering
4. Velg mål-warehouse (Snowflake, BigQuery, Fabric, osv.)
5. Konfigurer dbt-prosjektinnstillinger
6. Start migreringen - AI genererer modeller, tester og dokumentasjon`,
			"sv": `För att skapa en migrering:
1. Gå till Migreringar > Ny Migrering
2. Konfigurera din MSSQL-anslutning (host, databas, inloggningsuppgifter)
3. Välj tabeller att migrera
4. Välj ditt mål-warehouse (Snowflake, BigQuery, Fabric, etc.)
5. Konfigurera dbt-projektinställningar
6. Starta migreringen - AI genererar modeller, tester och dokumentation`,
		}
		if resp, ok := migrationResponses[language]; ok {
			return &ChatResponse{Response: resp}
		}
		return &ChatResponse{Response: migrationResponses["en"]}
	}

	// Multilingual default responses
	defaultResponses := map[string]string{
		"en": `I'm your DataMigrate AI Support Assistant. I can help with:
- Creating and managing migrations
- Database connection configuration
- Understanding dbt models
- Using AI agents
- Troubleshooting issues
What would you like to know more about?`,
		"da": `Jeg er din DataMigrate AI Support Assistent. Jeg kan hjælpe med:
- Oprettelse og administration af migreringer
- Konfiguration af databaseforbindelse
- Forståelse af dbt-modeller
- Brug af AI-agenter
- Fejlfinding
Hvad vil du gerne vide mere om?`,
		"de": `Ich bin Ihr DataMigrate AI Support-Assistent. Ich kann helfen bei:
- Erstellen und Verwalten von Migrationen
- Konfiguration von Datenbankverbindungen
- Verstehen von dbt-Modellen
- Nutzung von KI-Agenten
- Fehlerbehebung
Worüber möchten Sie mehr erfahren?`,
		"es": `Soy tu Asistente de Soporte DataMigrate AI. Puedo ayudarte con:
- Crear y gestionar migraciones
- Configuración de conexiones de base de datos
- Entender modelos dbt
- Usar agentes de IA
- Solucionar problemas
¿Qué te gustaría saber más?`,
		"pt": `Sou seu Assistente de Suporte DataMigrate AI. Posso ajudar com:
- Criar e gerenciar migrações
- Configuração de conexões de banco de dados
- Entender modelos dbt
- Usar agentes de IA
- Solucionar problemas
O que você gostaria de saber mais?`,
		"no": `Jeg er din DataMigrate AI Support-assistent. Jeg kan hjelpe med:
- Opprette og administrere migreringer
- Konfigurering av databasetilkobling
- Forstå dbt-modeller
- Bruke AI-agenter
- Feilsøking
Hva vil du vite mer om?`,
		"sv": `Jag är din DataMigrate AI Support-assistent. Jag kan hjälpa med:
- Skapa och hantera migreringar
- Konfigurering av databasanslutning
- Förstå dbt-modeller
- Använda AI-agenter
- Felsökning
Vad vill du veta mer om?`,
	}

	// Get response for language, fallback to English
	response, ok := defaultResponses[language]
	if !ok {
		response = defaultResponses["en"]
	}

	return &ChatResponse{Response: response}
}

// contains checks if s contains substr (case-insensitive)
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if equalFold(s[i:i+len(substr)], substr) {
			return true
		}
	}
	return false
}

func equalFold(s, t string) bool {
	if len(s) != len(t) {
		return false
	}
	for i := 0; i < len(s); i++ {
		sr := s[i]
		tr := t[i]
		if sr >= 'A' && sr <= 'Z' {
			sr += 'a' - 'A'
		}
		if tr >= 'A' && tr <= 'Z' {
			tr += 'a' - 'A'
		}
		if sr != tr {
			return false
		}
	}
	return true
}
