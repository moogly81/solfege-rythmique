# Comment écrire les rythmes dans `cahier.txt`

Tout le contenu du cahier est dans **`cahier.txt`** : chapitres, leçons, consignes et exercices. C'est un simple fichier texte, qu'on modifie avec n'importe quel éditeur (TextEdit en mode « texte brut », VS Code…). Pas besoin de toucher au programme.

Après chaque modification, régénérer le PDF :

```
python3 solfege_rythmique.py
```

Si quelque chose est faux (une mesure trop longue, un symbole inconnu), le programme s'arrête **sans rien casser** et indique où est l'erreur :

```
cahier.txt, ligne 52 (exercice 2.1.3), mesure 2 (b n n) : 4 temps au lieu de 3
```

Il suffit d'aller à la ligne 52, de corriger, puis de relancer.

---

## 1. Les symboles

Chaque note ou silence s'écrit avec une ou deux lettres, **séparées par des espaces**.

### Notes

| Écrire | Valeur | Durée | Astuce pour retenir |
|---|---|---|---|
| `r`  | ronde | 4 temps | **r**onde |
| `b.` | blanche pointée | 3 temps | le point, comme sur la partition |
| `b`  | blanche | 2 temps | **b**lanche |
| `n.` | noire pointée | 1 temps ½ | |
| `n`  | noire | 1 temps | **n**oire |
| `c.` | croche pointée | ¾ de temps | |
| `c`  | croche | ½ temps | **c**roche |
| `d`  | double-croche | ¼ de temps | **d**ouble |
| `t`  | croche de triolet | ⅓ de temps | **t**riolet, toujours par 3 : `t t t` |

### Silences

| Écrire | Valeur | Durée | Astuce |
|---|---|---|---|
| `p`  | pause | toute la mesure | **p**ause, toujours seule dans sa mesure |
| `dp` | demi-pause | 2 temps | **d**emi-**p**ause (comme `b`) |
| `s`  | soupir | 1 temps | **s**oupir (comme `n`) |
| `ds` | demi-soupir | ½ temps | **d**emi-**s**oupir (comme `c`) |

### Barre de mesure

`|` sépare les mesures (sur Mac : Option + Maj + L).

Exemple, une ligne de 4 mesures en 4/4 :

```
n n b | c c c c n n | r | n s dp
```

---

## 2. Ce qu'on n'a pas besoin d'écrire

- **Les ligatures** (les barres qui relient les croches) : automatiques, par temps. `c c c c` en 4/4 donne deux groupes de deux croches.
- **Les numéros** (chapitre 2, leçon 2.1, exercice 2.1.3) : automatiques. Si on insère un exercice, les suivants sont renumérotés.
- **La clé, le chiffrage, la double barre de fin** : ajoutés automatiquement à chaque exercice.

---

## 3. Structure du fichier

```
# Chapitre 2 : Le temps                      <- nouveau chapitre

## La noire                                  <- nouvelle leçon = une page A4
Consigne : Compte 1 - 2 - 3 - 4 : la noire dure 1 temps.
Mesure : 4/4                                 <- chiffrage de toute la leçon

- n n n n | n n n n | n n n n | n n n n      <- exercice sur 1 ligne
- n n b | b n n | r | n n n n                <- exercice sur 2 lignes :
  b b | n n b | p | n n n n                  <-   2e ligne décalée de 2 espaces
- 3/4 : b n | n n n | b. | p                 <- exercice avec son propre chiffrage

// Ceci est un commentaire : ignoré par le programme.
```

Règles :

- `# Chapitre N : titre` : le numéro écrit est ignoré, c'est l'ordre dans le fichier qui compte.
- `## titre` ouvre une leçon. Chaque leçon fait **une page**.
- `Consigne :` donne la phrase affichée sous le titre. Elle doit être courte : elle doit tenir sur une ligne.
- `Mesure :` vaut `2/4`, `3/4` ou `4/4`. Sans cette ligne, c'est `4/4`.
- `- ` (tiret, espace) commence un exercice. Un exercice fait **1 ou 2 lignes**.
- `3/4 :` au début d'un exercice change le chiffrage pour cet exercice seulement.
- Les lignes vides et les commentaires `//` sont libres : on en met autant qu'on veut.

---

## 4. Vérifications automatiques

Le programme refuse et explique :

- une mesure qui n'a pas le bon nombre de temps (4 en 4/4, 3 en 3/4, 2 en 2/4) ;
- un symbole inconnu (faute de frappe, par exemple `nn` au lieu de `n n`) ;
- un triolet incomplet ou décalé : `t t t` doit commencer sur un temps ;
- une pause `p` qui n'est pas seule dans sa mesure : pour 2 temps de silence, écrire `dp` ;
- un exercice de plus de 2 lignes ;
- du texte mal placé (par exemple une ligne d'exercice sans `- ` devant).

---

## 5. Limites de mise en page

Le programme vérifie les rythmes, **pas la place sur la page**. Pour que chaque leçon tienne sur une feuille :

- 6 à 10 lignes de musique par leçon (4 à 6 exercices) ;
- nombre de mesures par ligne :

| Chiffrage | Ligne normale | Ligne chargée (croches, doubles ou triolets partout) |
|---|---|---|
| 4/4 | 4 mesures | 3 mesures |
| 3/4 | 4 mesures | 3 mesures |
| 2/4 | 4 à 6 mesures | 4 mesures |

Si une page déborde, le PDF aura une page de plus que prévu. Dans ce cas, raccourcir une ligne ou supprimer un exercice.

---

## 6. Exemples de rythmes courants

| Rythme | Écrire | Dure |
|---|---|---|
| 2 croches | `c c` | 1 temps |
| 4 doubles | `d d d d` | 1 temps |
| croche + 2 doubles | `c d d` | 1 temps |
| 2 doubles + croche | `d d c` | 1 temps |
| croche pointée + double | `c. d` | 1 temps |
| triolet | `t t t` | 1 temps |
| noire pointée + croche | `n. c` | 2 temps |
| demi-soupir + croche | `ds c` | 1 temps |
