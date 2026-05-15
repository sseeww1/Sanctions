# Guide des commandes du bot

Prefix utilise : `+`

## Permissions

Les administrateurs ont toujours acces a toutes les commandes. Si une commande a au moins un role configure avec `+addperm` ou le panel, seuls les roles configures peuvent l'utiliser, en plus des administrateurs.

- `+panel` : ouvre un panel Discord avec menus et boutons pour ajouter ou retirer des roles autorises sur une commande.
- `+addperm @role commande` : autorise un role a utiliser une commande.
- `+delperm @role commande` : retire l'autorisation speciale d'un role.
- `+listperms` : affiche toutes les permissions speciales configurees sur le serveur.

## Aide

- `+help` : affiche toutes les commandes disponibles.
- `+helpall` : affiche les commandes classees par categories de permissions.
- `+info` : affiche un guide staff en plusieurs embeds.

## Moderation

- `+warn @membre raison` : ajoute un avertissement en base de donnees.
- `+sanctions @membre` : affiche les 10 dernieres sanctions d'un membre.
- `+delsanction ID` : supprime une sanction precise.
- `+clearsanctions @membre` : supprime toutes les sanctions et warns d'un membre.
- `+mute @membre minutes raison` : met un membre en timeout Discord.
- `+unmute @membre raison` : retire le timeout Discord.
- `+clear nombre` : supprime entre 1 et 100 messages.
- `+lock #salon` : verrouille un salon. Si aucun salon n'est donne, verrouille le salon actuel.
- `+unlock #salon` : deverrouille un salon. Si aucun salon n'est donne, deverrouille le salon actuel.

## Ban et sanctions fortes

- `+kick @membre raison` : expulse un membre.
- `+ban @membre raison` : bannit un membre.
- `+unban ID raison` : debannit un utilisateur avec son ID.
- `+baninfo ID` : affiche les informations Discord et bot sur un ban.

## Blacklist bot

- `+bl @membre raison` : empeche un membre d'utiliser le bot sur le serveur.
- `+unbl @membre` : retire un membre de la blacklist bot.
- `+blinfo @membre` : affiche les informations de blacklist.

## Utilitaires

- `+avatar @utilisateur` : affiche l'avatar d'un utilisateur.
- `+banner @utilisateur` : affiche la banniere d'un utilisateur si elle existe.
- `+userinfo @membre` : affiche les informations d'un membre.
- `+serverinfo` : affiche les informations du serveur.
