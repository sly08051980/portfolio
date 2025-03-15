const express = require("express");
const app = express();
const fs = require("fs");
const bodyParser = require("body-parser");
const jsonPokemon = require("./pokemonList.json");
const { log } = require("console");

class CartePokemon {
  static cartesPokemon = new Map();

  constructor(nom, type, imageSrc) {
    this.id = jsonPokemon.length + 1;
    this.nom = nom;
    this.type = type;
    this.imageSrc = imageSrc;

    if (CartePokemon.cartesPokemon.has(this.id)) {
      throw new Error("Une carte avec cet ID existe déjà.");
    }

    CartePokemon.cartesPokemon.set(this.id, this);
  }

  static getNextId() {
    console.log("test", CartePokemon.cartesPokemon.size);
    return CartePokemon.cartesPokemon.size + 1;
  }
}

const port = 3000;
app.use(express.static("public"));
app.use(express.json());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.listen(port, () => {
  console.log(`Écoute http://localhost:${port}`);
});

app.get("/", (req, res) => {
  res.sendFile(__dirname + "/public/index.html");
});

app.get("/pokemonList", (req, res) => {
  res.sendFile(__dirname + "/pokemonList.json");
});

app.get("/cartes", (req, res) => {
  const nom = req.query.nom;
  if (!nom) {
    return res.status(400).json({ erreur: "saisir un nom " });
  }
  const pokemonChoisi = jsonPokemon.find((pokemon) => pokemon.nom === nom);
  if (pokemonChoisi) {
    res.json(pokemonChoisi);
  } else {
    res.status(404).json({ erreur: `${nom} n est pas un pokemon valide` });
  }
});
app.put("/modifier/:id",(req,res)=>{
  const putID=parseInt(req.params.id);
  const putNom =req.body.nom;
  const putType=req.body.type;
  const putImage = req.body.image;

  console.log(putID);
  console.log(putNom);
  console.log(putType);
  console.log(putImage);
  const modifierId = jsonPokemon.findIndex(item => item.id === putID);
  console.log("modifier : ",modifierId);
  
  if (modifierId !== -1) {
    jsonPokemon[modifierId].nom = putNom;
    jsonPokemon[modifierId].type = putType;
    jsonPokemon[modifierId].image = putImage;

    console.log("ok");
    res.json({ success: true, message: 'ok' });
    fs.writeFile(
      "pokemonList.json",
      JSON.stringify(jsonPokemon),
      function (err) {
        if (err) {
          return console.log(err);
        }
      }
    );
  } else {
    console.log("Pokemon non trouve avec cet ID.");
    res.status(404).json({ success: false, message: 'Pokemon non trouve avec cet ID.' });
  }

})
app.delete("/delete/:id", (req, res) => {
  const deleteId = parseInt(req.params.id);
  console.log(deleteId);

  const suppId = jsonPokemon.findIndex((item) => item.id === deleteId);

  if (suppId !== -1) {
    jsonPokemon.splice(suppId, 1);
    console.log(jsonPokemon);
    fs.writeFile(
      "pokemonList.json",
      JSON.stringify(jsonPokemon),
      function (err) {
        if (err) {
          return console.log(err);
        }
      }
    );
    res.json({ success: true, message: "Pokemon supprime avec succès." });
  } else {
    res
      .status(404)
      .json({ success: false, message: "Pokemon non trouve avec cet ID." });
  }
});

app.post("/cartes", (req, res) => {
  const nom = req.body.nom;
  const type = req.body.type;
  const image = req.body.imageSrc;

  let jsonData = [];
  fs.readFile("pokemonList.json", "utf8", function (err, data) {
    if (err) {
      return console.error(err);
    }

    jsonData = JSON.parse(data);

    const carte = new CartePokemon(nom, type, image);
    jsonData.push(carte);

    fs.writeFile("pokemonList.json", JSON.stringify(jsonData), function (err) {
      if (err) {
        return console.error(err);
      }
      console.log("Fichier ajouté");
      res.sendFile(__dirname + "/public/index.html");
    });
  });
});
