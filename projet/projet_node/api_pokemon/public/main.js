document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM chargé");
console.log("dom chargé");

afficherPokemon();

let affiche = false;

async function afficherPokemon() {
  fetch("/pokemonList")
    .then((response) => {
      if (!response.ok) {
        throw new Error("pas d internet");
      }
      return response.json();
    })
    .then((jsonData) => {
      jsonData.forEach((element) => {
        let pokemonId = element.id;

        let pokemonTr = document.createElement("tr");
        let pokemonNomTd = document.createElement("td");
        pokemonNomTd.innerHTML = element.nom;
        pokemonTr.appendChild(pokemonNomTd);

        let pokemonTypeTd = document.createElement("td");
        pokemonTypeTd.innerHTML = element.type;
        pokemonTr.appendChild(pokemonTypeTd);

        let pokemonImageTd = document.createElement("td");
        let pokemonImage = document.createElement("img");
        pokemonImage.src = element.imageSrc;
        pokemonImageTd.appendChild(pokemonImage);
        pokemonTr.appendChild(pokemonImageTd);

        let pokemonDelete = document.createElement("button");
        pokemonDelete.setAttribute("class", "supprimer");
        pokemonTr.appendChild(pokemonDelete);

        let pokemonModifier = document.createElement("button");
        pokemonModifier.setAttribute("class", "modifier");
        pokemonTr.appendChild(pokemonModifier);

        let pokemonTable = document.getElementById("pokemonList");
        pokemonTable.appendChild(pokemonTr);

        pokemonDelete.addEventListener("click", function (event) {
          deletePokemon(pokemonId);
        });
        pokemonModifier.addEventListener("click", function (event) {
          console.log("click modifier");
          modifierPokemon(element);
        });
      });
    })
    .catch((error) => console.error("Fetch error:", error));
}

function deletePokemon(pokemonId) {
  console.log("click");
  console.log(pokemonId);

  fetch(`/delete/${pokemonId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => {
      if (response.ok) {
        console.log(`Suppression du pokemon : ${pokemonId} reussit`);
        location.reload();
      } else {
        console.error("Échec de la suppression du Pokémon.");
      }
    })
    .catch((error) => {
      console.error("Erreur lors de la suppression:", error);
    });
}

function modifierPokemon(element) {
  let modifierId;
  let modifierButton;
  if (!affiche) {
    let modifierForm = document.createElement("form");
    // modifierForm.setAttribute("action", "/modifier");
    // modifierForm.setAttribute("name", "modifier");
    // modifierForm.setAttribute("method", "POST");

    modifierId=document.createElement("input");
    modifierId.setAttribute("type","hidden");
    modifierId.setAttribute("id","id");

    let labelNom = document.createElement("label");
    labelNom.setAttribute("for", "modifierNom");
    labelNom.innerHTML = "Nom :";
    let modifierNom = document.createElement("input");
    modifierNom.setAttribute("type", "text");
    modifierNom.setAttribute("id", "modifierNom");
    modifierNom.setAttribute("name", "modifierNom");

    let card = document.getElementById("card");
    card.appendChild(modifierForm);
    modifierForm.appendChild(modifierId);
    modifierForm.appendChild(labelNom);
    modifierForm.appendChild(modifierNom);

    let labelType = document.createElement("label");
    labelType.setAttribute("for", "modifierType");
    labelType.innerHTML = "Type : ";
    let modifierType = document.createElement("input");
    modifierType.setAttribute("type", "text");
    modifierType.setAttribute("id", "modifierType");
    modifierType.setAttribute("name", "modifierType");
    modifierForm.appendChild(labelType);
    modifierForm.appendChild(modifierType);

    let labelImage = document.createElement("label");
    labelImage.setAttribute("for", "modifierImage");
    labelImage.innerHTML = "Src Image : ";
    let modifierImage = document.createElement("input");
    modifierImage.setAttribute("type", "text");
    modifierImage.setAttribute("id", "modifierImage");
    modifierImage.setAttribute("name", "modifierImage");
    modifierForm.appendChild(labelImage);
    modifierForm.appendChild(modifierImage);

     modifierButton = document.createElement("button");
    modifierButton.setAttribute("type", "submit");
    modifierButton.innerHTML = "modifier";
    modifierForm.appendChild(modifierButton);
    affiche = true;
  } else {
    modifierNom.value = "";
    modifierType.value = "";
    modifierImage.value = "";
    modifierId.value="";
  }
  modifierNom.value = element.nom;
  modifierType.value = element.type;
  modifierImage.value = element.imageSrc;
 modifierId.value=element.id;
modifierButton.addEventListener("click", function (event){
  putPokemon(modifierId,modifierNom,modifierType,modifierImage);
})

}

function putPokemon(modifierId,modifierNom,modifierType,modifierImage){
  console.log(modifierId.value);
  console.log(modifierNom.value);
  console.log(modifierType.value);
  console.log(modifierImage.value);
  fetch(`/modifier/${modifierId.value}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body:JSON.stringify({
      nom:modifierNom.value,
      type:modifierType.value,
      image:modifierImage.value
      
    })
  })
    .then((response) => {
      if (response.ok) {
        console.log(`le pokemon  ${pokemonId} a été modifié.`);
        location.reload();
      } else {
        console.error("Échec de la modification du Pokémon.");
      }
    })
    .catch((error) => {
      console.error("Erreur lors de la modification:", error);
    });
}

  document.forms.onePoke.addEventListener("submit", function(e) {
    e.preventDefault(); // Empêche la soumission classique
    const nomRecherche = document.getElementById("nomCarte").value.trim();

    fetch(`/cartes?nom=${encodeURIComponent(nomRecherche)}`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Aucun Pokémon trouvé ou erreur dans la requête");
        }
        return response.json();
      })
      .then(data => {
        // Vider le tableau pour n'afficher que le Pokémon recherché
        const pokemonTable = document.getElementById("pokemonList");
        pokemonTable.innerHTML = "";
        // Créer une nouvelle ligne
        let pokemonTr = document.createElement("tr");

        let pokemonNomTd = document.createElement("td");
        pokemonNomTd.textContent = data.nom;
        pokemonTr.appendChild(pokemonNomTd);

        let pokemonTypeTd = document.createElement("td");
        pokemonTypeTd.textContent = data.type;
        pokemonTr.appendChild(pokemonTypeTd);

        let pokemonImageTd = document.createElement("td");
        let pokemonImage = document.createElement("img");
        pokemonImage.src = data.imageSrc;
        pokemonImageTd.appendChild(pokemonImage);
        pokemonTr.appendChild(pokemonImageTd);

        // Vous pouvez ajouter des boutons si nécessaire
        pokemonTable.appendChild(pokemonTr);
      })
      .catch(error => {
        console.error("Erreur lors de l'affichage du Pokémon:", error);
        document.getElementById("pokemonList").innerHTML =
          `<tr><td colspan="4">${error.message}</td></tr>`;
      });
  });
});
