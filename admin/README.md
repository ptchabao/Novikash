# NoviKash Admin

Console d'administration Next.js + shadcn/ui pour gérer la plateforme NoviKash.

## Prérequis

- Node.js 20+
- API NoviKash en cours d'exécution
- Compte staff (`SUPERADMIN`, `ADMIN`, `SUPPORT` ou `AUDITOR`)

## Configuration

```bash
cp .env.local.example .env.local
# Éditer NEXT_PUBLIC_API_URL (ex: http://localhost:8000)
```

## Créer un SuperAdmin (API)

```bash
cd ..
./venv/bin/python create_admin.py +22890000000 MotDePasseSecret
```

## Lancer

```bash
npm install
npm run dev
```

Ouvrir [http://localhost:3000](http://localhost:3000) — connexion avec le téléphone et mot de passe admin.

### Lanceur pratique

```bash
./start-admin.sh dev
```

> Le script initialise `.env.local` si nécessaire, installe les dépendances, et lance le serveur.

## Docker

Depuis le dossier `admin` :

```bash
docker build -t novikash-admin \
  --build-arg NEXT_PUBLIC_API_URL=https://votre-api.novikash.com \
  .

docker run -p 3000:3000 novikash-admin
```

`NEXT_PUBLIC_API_URL` est injectée au **build** (variable publique Next.js). Pour changer l’URL API, reconstruire l’image.

Push vers un registry :

```bash
docker tag novikash-admin votre-registry/novikash-admin:latest
docker push votre-registry/novikash-admin:latest
```

## Rôles et permissions

| Rôle | Accès |
|------|--------|
| **SUPERADMIN** | Tout + configuration système + gestion des rôles |
| **ADMIN** | Utilisateurs, wallets (crédit/débit), transactions, prêts, KYC, NOVI+ |
| **SUPPORT** | Lecture + validation KYC |
| **AUDITOR** | Lecture seule (dashboard, users, transactions, loans) |

## Fonctionnalités

- Tableau de bord (stats temps réel)
- Utilisateurs et détail compte
- **Crédit / débit manuel** sur wallet
- Transactions (filtres type/statut)
- Prêts NOVI+ / ALOBA (changement de statut)
- Validation profils NOVI+ (banque)
- File KYC
