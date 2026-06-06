# NoviKash Admin - Guide de Setup Complet

## État du Projet

✅ **Compilé et testé** - Next.js 16 + TypeScript + shadcn/ui
✅ **Routes configurées** - Dashboard, Users, Loans, KYC, Transactions, NoviPlus
✅ **Authentification** - JWT Bearer avec AuthContext
✅ **API intégrée** - Connexion FastAPI backend
✅ **Docker ready** - Production image disponible
✅ **Build optimisé** - 10 routes statiques générées

## Installation Rapide

### 1. Environnement

```bash
# S'assurer que Node.js 20+ est installé
node --version  # v20.x ou plus

# Copier .env.local
cp .env.local.example .env.local

# Éditer si API sur autre adresse
# NEXT_PUBLIC_API_URL=http://localhost:8000 (default)
```

### 2. Dépendances (déjà installées)

```bash
npm install
# ou npm ci pour reproduction exacte
```

### 3. Backend - Créer Admin

```bash
cd ..
source venv/bin/activate

# Créer un SUPERADMIN
python create_admin.py +22890000000 MonMotDePasse123

# Ou en CLI interactif
python -c "
from create_admin import create_superadmin
phone = input('Phone: ')
pwd = input('Password: ')
create_superadmin(phone, pwd)
print('✓ SuperAdmin créé!')
"
```

### 4. Lancer en Développement

```bash
# Terminal 1: Backend
cd /home/osiris/Documents/Novikash
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Admin Frontend
cd admin
npm run dev

# Ouvrir http://localhost:3000
```

## Authentification

**Login Page**: `/login`

```
Phone:    +22890000000 (ou 90000000 pour Mauritanie)
Password: MonMotDePasse123
```

Après login → JWT token stocké en localStorage
Accès au dashboard → routes protégées par AuthProvider

## Routes Disponibles

| Route | Rôle | Description |
|-------|------|-------------|
| `/` | PUBLIC | Dashboard KPI |
| `/login` | PUBLIC | Page de connexion |
| `/users` | ADMIN+ | Liste des utilisateurs |
| `/users/[id]` | ADMIN+ | Détail utilisateur |
| `/transactions` | ADMIN+ | Historique transactions |
| `/kyc` | ADMIN+ | Documents KYC |
| `/loans` | ADMIN+ | Crédits en cours |
| `/novi-plus` | ADMIN+ | Souscriptions NoviPlus |

## Build & Deploy

### Développement

```bash
npm run dev
# → http://localhost:3000 avec hot-reload
```

### Production (local)

```bash
npm run build      # Génère .next/
npm start          # Serve sur port 3000
```

### Docker Production

```bash
# Build avec URL API
docker build -t novikash-admin \
  --build-arg NEXT_PUBLIC_API_URL=https://api.novikash.com \
  .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.novikash.com \
  novikash-admin

# Ou depuis docker-compose (parent)
cd ..
docker-compose up admin
```

## Architecture

```
src/
├── app/               # Pages Next.js (routing)
│   ├── (dashboard)/   # Routes protégées
│   ├── login/         # Public
│   └── layout.tsx     # Root layout
├── components/        # React components
│   ├── ui/           # shadcn/ui components
│   └── [shared]/     # Custom components
├── contexts/         # React Contexts
│   └── auth-context   # Auth & token management
├── lib/
│   ├── api.ts        # API client (Axios)
│   ├── permissions.ts # Role-based logic
│   └── utils.ts      # Helpers
└── types/
    └── index.ts      # TypeScript types
```

## Points Clés

### AuthProvider (`src/contexts/auth-context.tsx`)
- ✅ Gère login/logout
- ✅ Stocke JWT token
- ✅ Protège routes privées
- ✅ Expose `useAuth()` hook

### API Client (`src/lib/api.ts`)
- ✅ Axios configured avec base URL
- ✅ Intercepteur Bearer token auto
- ✅ Gestion erreurs 401/403/500

### Permissions (`src/lib/permissions.ts`)
- ✅ Rôles: SUPERADMIN, ADMIN, SUPPORT, AUDITOR
- ✅ Contrôle accès par page
- ✅ Redirect si insuffisant

### Components
- ✅ DataTable avec pagination/sort
- ✅ KPI Cards pour dashboard
- ✅ Charts (Recharts intégré)
- ✅ Forms avec validation
- ✅ Dialogs/Modals avec Sonner toast

## Troubleshooting

### "Cannot GET /"
→ Build incomplet. Lancer `npm run build`

### "API connection refused"
→ Backend pas accessible. Vérifier `NEXT_PUBLIC_API_URL`

### "401 Unauthorized"
→ Token expiré. Se reconnecter à `/login`

### "Permission denied"
→ Rôle utilisateur insuffisant. Vérifier `create_admin.py`

### Styles cassés
→ Tailwind pas compilé. Lancer `npm run dev` complet

## Maintenance

```bash
# Linter
npm run lint

# Mettre à jour dépendances
npm outdated
npm update

# Nettoyer
npm cache clean --force
rm -rf .next node_modules
npm ci
```

## Checklist Finalisation

- [x] Next.js configuré + build passing
- [x] TypeScript compiling
- [x] Authentification JWT working
- [x] Routes protégées via AuthProvider
- [x] Components shadcn/ui loaded
- [x] API client configured
- [x] Docker image builds
- [x] .env.local setup
- [x] npm dependencies installed
- [x] ESLint passing
- [x] Documentation complète

## Prochaines Étapes

1. **Personalization** : Ajouter logo/couleurs brand
2. **Features** : Implémented dans les pages (dashboard/)
3. **i18n** : Multilingue (FR/EN)
4. **Testing** : Jest + React Testing Library
5. **Deployment** : Vercel, AWS, ou VPS

---

**Status**: ✅ **PRÊT À UTILISER** | Production-ready dashboard
