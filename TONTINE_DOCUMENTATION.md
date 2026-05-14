# Module Tontine - Documentation Complète

## Vue d'ensemble

Le module **Tontine** est un système de compte d'épargne bloqué qui permet aux utilisateurs d'économiser de l'argent en le bloquant pour une période déterminée (10, 20 ou 30 jours).

### Caractéristiques principales:
- **Compte d'épargne dédié**: Solde séparé du portefeuille principal
- **Blocage flexible**: Choix entre 10, 20 ou 30 jours
- **Protection des fonds**: Les fonds bloqués ne peuvent pas être retirés
- **Versements continus**: Ajout de fonds possible même pendant le blocage
- **Sécurité**: Modification de la durée interdite pendant le blocage

---

## Architecture Backend

### **1. Modèles de données** (`app/models/models.py`)

#### Classe `Tontine`
```python
class Tontine(SQLModel, table=True):
    id: Optional[int]
    user_id: int (FK → user.id, unique)
    balance: float (solde de la tontine)
    currency: str (défaut: "XOF")
    status: str (ACTIVE, LOCKED, UNLOCKED)
    lock_duration_days: int (10, 20, 30)
    lock_start_date: Optional[datetime]
    lock_end_date: Optional[datetime]
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    
    relationships:
    - user: User (back_populates="tontine")
    - transactions: List[TontineTransaction]
```

#### Classe `TontineTransaction`
```python
class TontineTransaction(SQLModel, table=True):
    id: Optional[int]
    tontine_id: int (FK → tontine.id)
    type: str (DEPOSIT, INTEREST)
    amount: float
    currency: str
    status: str (SUCCESS, FAILED)
    reference: str (unique)
    description: Optional[str]
    created_at: datetime
```

### **2. Schémas Pydantic** (`app/schemas/schemas.py`)

- **TontineRead**: Réponse pour récupérer la tontine
- **TontineCreate**: Création initiale (non utilisée actuellement)
- **TontineDepositRequest**: Demande de dépôt
- **TontineLockRequest**: Demande de blocage (avec `lock_duration_days`)
- **TontineTransactionRead**: Affichage des transactions

### **3. API Endpoints** (`app/api/tontine.py`)

| Endpoint | Méthode | Description | Authentification |
|----------|---------|-------------|------------------|
| `/tontine/me` | GET | Récupère la tontine de l'utilisateur | ✓ |
| `/tontine/deposit` | POST | Dépôt depuis le portefeuille principal | ✓ |
| `/tontine/lock` | POST | Bloque la tontine pour la durée spécifiée | ✓ |
| `/tontine/transactions` | GET | Liste toutes les transactions | ✓ |
| `/tontine/status` | GET | Statut détaillé avec temps restant | ✓ |

#### Endpoints détaillés

##### `POST /tontine/deposit`
Dépose des fonds du portefeuille principal vers la tontine
```json
Request:
{
  "amount": 50000
}

Response:
{
  "id": 1,
  "type": "DEPOSIT",
  "amount": 50000,
  "currency": "XOF",
  "status": "SUCCESS",
  "reference": "TONT-DEP-ABC123",
  "description": "Deposit from main wallet",
  "created_at": "2024-05-14T10:30:00"
}
```

##### `POST /tontine/lock`
Bloque la tontine pour une période
```json
Request:
{
  "lock_duration_days": 30
}

Validation:
- Durée doit être 10, 20 ou 30 jours
- Tontine ne doit pas déjà être bloquée
- Solde doit être > 0

Response: Tontine object avec is_locked=true et lock_end_date définie
```

##### `GET /tontine/status`
Retourne le statut avec temps restant en secondes
```json
Response:
{
  "id": 1,
  "balance": 50000,
  "is_locked": true,
  "status": "LOCKED",
  "lock_duration_days": 30,
  "lock_start_date": "2024-05-14T10:30:00",
  "lock_end_date": "2024-06-13T10:30:00",
  "time_remaining_seconds": 2592000,
  "created_at": "2024-05-14T10:30:00",
  "updated_at": "2024-05-14T10:30:00"
}
```

### **4. Intégration au routeur principal**

Dans `app/main.py`:
```python
from app.api import tontine
app.include_router(tontine.router, prefix="/tontine", tags=["Tontine"])
```

---

## Architecture Frontend (Flutter)

### **1. Modèles** (`lib/models/tontine.dart`)

#### Classe `Tontine`
Représentation de la tontine avec méthodes utilitaires:
- `getTimeRemainingSeconds()`: Retourne le temps en secondes
- `getTimeRemainingString()`: Formatte le temps restant (ex: "3 days, 5 hours")

#### Classe `TontineStatus`
Statut détaillé avec temps restant calculé

#### Classe `TontineTransaction`
Représentation des transactions

### **2. Service API** (`lib/services/api_service.dart`)

Méthodes ajoutées:
```dart
Future<Response> getTontine()
Future<Response> depositToTontine(double amount)
Future<Response> lockTontine(int lockDurationDays)
Future<Response> getTontineTransactions()
Future<Response> getTontineStatus()
```

### **3. Provider** (`lib/providers/tontine_provider.dart`)

`TontineProvider` extends `ChangeNotifier`

**Propriétés:**
- `tontine`: Instance actuelle de Tontine
- `tontineStatus`: Statut détaillé
- `isLoading`: État de chargement
- `error`: Message d'erreur
- `transactions`: Liste des transactions
- `hasActiveTontine`: Si balance > 0
- `isTontineLocked`: Si bloquée

**Méthodes:**
- `fetchTontine()`: Récupère la tontine
- `fetchTontineStatus()`: Récupère le statut
- `depositToTontine(amount)`: Dépôt
- `lockTontine(lockDurationDays)`: Blocage
- `fetchTransactions()`: Récupère les transactions
- `refreshTontineData()`: Rafraîchit tout

### **4. Interface UI** (`lib/ui/screens/tontine_screen.dart`)

Page complète `TontineScreen` avec:

**Sections:**
1. **Carte de solde**: Affiche le solde actuel avec gradient
2. **Info blocage**: Messages d'avertissement/confirmation selon l'état
3. **Boutons d'action**: 
   - "Ajouter des fonds" (toujours actif)
   - "Bloquer ma tontine" (désactivé si déjà bloquée)
4. **Historique transactions**: Liste les dépôts et intérêts

**Dialogues:**
- **Dialogue de dépôt**: Saisie du montant
- **Dialogue de blocage**: Sélection de la durée (10/20/30 jours)

### **5. Intégration au Dashboard**

Dans `lib/ui/screens/dashboard_screen.dart`:
- Ajout du bouton "Tontine" dans la grille d'actions (couleur pourpre)
- Navigation vers `TontineScreen`
- Import de `tontine_screen.dart`

### **6. Configuration du Provider**

Dans `lib/main.dart`:
```dart
MultiProvider(
  providers: [
    ChangeNotifierProvider.value(value: authProvider),
    ChangeNotifierProvider(create: (_) => TontineProvider()),
  ],
  ...
)
```

---

## Flux utilisateur

### **Créer une Tontine:**
1. L'utilisateur accède au dashboard
2. Clique sur le bouton "Tontine"
3. La tontine est créée automatiquement s'il n'en a pas

### **Ajouter des fonds:**
1. Clique sur "Ajouter des fonds"
2. Saisit le montant
3. Les fonds sont déduits du portefeuille principal
4. Transaction enregistrée

### **Bloquer la Tontine:**
1. Clique sur "Bloquer ma tontine"
2. Sélectionne la durée (10/20/30 jours)
3. Confirme
4. Compte bloqué jusqu'à la date d'expiration
5. Retrait impossible, ajout possible

### **Après le déblocage:**
- `lock_end_date` atteint
- `is_locked` passe à `false`
- `status` passe à `ACTIVE`
- L'utilisateur peut à nouveau bloquer ou ajouter des fonds

---

## Sécurité et Validations

### **Backend:**
- Validation du montant > 0
- Vérification du solde disponible
- Durée de blocage limitée à [10, 20, 30]
- Empêche le blocage si déjà bloquée
- Débloquage automatique après expiration

### **Frontend:**
- Validation du montant
- Messages d'erreur clairs
- Bouton "Bloquer" désactivé si déjà bloquée
- Affichage de l'avertissement pendant le blocage

---

## Améliorations futures

- [ ] Calcul d'intérêts automatiques
- [ ] Notifications de déblocage
- [ ] Réclamation automatique après déblocage
- [ ] Rapports d'épargne
- [ ] Cible d'épargne personnalisée
- [ ] Plusieurs tontines avec noms
- [ ] Partage de tontine (groupe)

---

## Tests recommandés

### **Backend:**
```bash
# Créer une tontine
POST /tontine/me

# Déposer des fonds
POST /tontine/deposit
{"amount": 10000}

# Bloquer pour 10 jours
POST /tontine/lock
{"lock_duration_days": 10}

# Vérifier le statut
GET /tontine/status

# Essayer de bloquer à nouveau (devrait échouer)
POST /tontine/lock
{"lock_duration_days": 20}
```

### **Frontend:**
- Naviguer vers la page Tontine
- Ajouter 10 000 XOF
- Bloquer pour 30 jours
- Vérifier le temps restant
- Tenter un dépôt supplémentaire (devrait fonctionner)
- Tenter un déblocage (devrait échouer)

---

## Fichiers modifiés/créés

### Backend:
- ✅ `app/models/models.py` - Ajout de `Tontine` et `TontineTransaction`
- ✅ `app/schemas/schemas.py` - Ajout des schémas Tontine
- ✅ `app/api/tontine.py` - Création (nouvel endpoint)
- ✅ `app/main.py` - Intégration du routeur

### Frontend:
- ✅ `novikash_app/lib/models/tontine.dart` - Modèles (création)
- ✅ `novikash_app/lib/providers/tontine_provider.dart` - Provider (création)
- ✅ `novikash_app/lib/services/api_service.dart` - Endpoints API
- ✅ `novikash_app/lib/ui/screens/tontine_screen.dart` - Page UI (création)
- ✅ `novikash_app/lib/ui/screens/dashboard_screen.dart` - Intégration bouton
- ✅ `novikash_app/lib/main.dart` - Configuration Provider

---

## Installation & Déploiement

### **1. Exécuter les migrations:**
```bash
cd /home/osiris/Documents/Novikash
# Les modèles sont automatiquement créés dans la base de données
```

### **2. Redémarrer l'API:**
```bash
# L'import du router au main.py active automatiquement les endpoints
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

### **3. Vérifier les endpoints:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/tontine/me
```

### **4. Déployer Flutter:**
```bash
cd novikash_app
flutter pub get
flutter run
```

---

**Module Tontine créé le**: 2024-05-14  
**Statut**: ✅ Complet et intégré
