const express = require("express");
const app = express();
const fs = require("fs");
const bodyParser = require("body-parser");
const jsonPokemon = require("./pokemonList.json");

// Middleware
app.use(express.static(__dirname + "/public"));
app.use(express.json());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Créer un router avec toutes les routes API
const apiRouter = express.Router();

// GET all Pokémon
apiRouter.get("/pokemon", (req, res) => {
  res.json(jsonPokemon);
});

// GET Pokémon by name
apiRouter.get("/cartes", (req, res) => {
  const nom = req.query.nom;
  if (!nom) {
    return res.status(400).json({ erreur: "Saisir un nom" });
  }
  const pokemonChoisi = jsonPokemon.find((pokemon) => pokemon.nom === nom);
  if (pokemonChoisi) {
    res.json(pokemonChoisi);
  } else {
    res.status(404).json({ erreur: `${nom} n'est pas un Pokémon valide` });
  }
});

// Modifier un Pokémon
apiRouter.put("/modifier/:id", (req, res) => {
  const putID = parseInt(req.params.id);
  const putNom = req.body.nom;
  const putType = req.body.type;
  const putImage = req.body.image;

  const modifierId = jsonPokemon.findIndex(item => item.id === putID);
  if (modifierId !== -1) {
    jsonPokemon[modifierId].nom = putNom;
    jsonPokemon[modifierId].type = putType;
    jsonPokemon[modifierId].image = putImage;

    fs.writeFile("pokemonList.json", JSON.stringify(jsonPokemon), function (err) {
      if (err) return console.log(err);
      res.json({ success: true, message: "Pokémon modifié avec succès" });
    });
  } else {
    res.status(404).json({ success: false, message: "Pokémon non trouvé avec cet ID." });
  }
});

// Supprimer un Pokémon
apiRouter.delete("/delete/:id", (req, res) => {
  const deleteId = parseInt(req.params.id);
  const suppId = jsonPokemon.findIndex(item => item.id === deleteId);

  if (suppId !== -1) {
    jsonPokemon.splice(suppId, 1);
    fs.writeFile("pokemonList.json", JSON.stringify(jsonPokemon), function (err) {
      if (err) return console.log(err);
      res.json({ success: true, message: "Pokémon supprimé avec succès." });
    });
  } else {
    res.status(404).json({ success: false, message: "Pokémon non trouvé avec cet ID." });
  }
});

// Ajouter un Pokémon
apiRouter.post("/cartes", (req, res) => {
  const nom = req.body.nom;
  const type = req.body.type;
  const image = req.body.imageSrc;

  fs.readFile("pokemonList.json", "utf8", function (err, data) {
    if (err) return console.error(err);
    let jsonData = JSON.parse(data);
    jsonData.push({ id: jsonData.length + 1, nom, type, image });

    fs.writeFile("pokemonList.json", JSON.stringify(jsonData), function (err) {
      if (err) return console.error(err);
      res.sendFile(__dirname + "/public/index.html");
    });
  });
});

// Monter le router sous le préfixe /api
app.use("/api", apiRouter);

// Page d'accueil
app.get("/", (req, res) => {
  res.sendFile(__dirname + "/public/index.html");
});

// Démarrage du serveur
const port = 3000;
app.listen(port, "0.0.0.0", () => {
  console.log(`✅ API dispo sur http://localhost:${port}/api/pokemon`);
});
