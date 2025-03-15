console.log("chargé");
let unPokemon = {};
let dataFetchTer= await getPokemonsList();
const listePokemons=dataFetchTer;
let url ="https://pokebuildapi.fr/api/v1/types";
let dataPokemonAttribut = await getPokemonsAttribut();
const listAttributPokemon= dataPokemonAttribut;
let attributPokemon={};
 const listPokemonByAttr= document.querySelector("#attr");
 const listPokemonByNom= document.querySelector("#liste")
 let selectList= document.querySelector('select');
 let stats = document.querySelector(".stats");
 let attributAffichage = document.createElement("div");
 let AttributPokemonAttribut = "";
 let pokemonChoisiAttribut ="";
 let pokemonChoisi="";


// console.log("voici les donnée via fetch avce promesse explicite :",dataFetchTer);


// Génération des options de la Select
let listeDeroulante= document.querySelector('select');

choixOption();
garnirSelectList();
verifListChecked();



function choixOption() {

    listeDeroulante.addEventListener('change', function () {
        stats.classList.replace('attr', 'stats');
        if (!listPokemonByAttr.checked){
        
        
        stats = document.querySelector(".stats");
       
        document.querySelector(".stats").innerHTML="";
        
      pokemonFunction();
     
         }else if (listPokemonByAttr.checked){

            const attr = listeDeroulante.value;
            // console.log(    "attribut ",attr);
            stats.innerHTML = '';
            const pokemonAttribut = dataFetchTer.filter(pokemon => {
                return pokemon.apiTypes.some(type => type.name === attr);
              });
        
            //  console.log("attribut :" ,pokemonAttribut);

            attributFunction(pokemonAttribut);
          

        }
    
    } 
    );
}


function pokemonFunction() {
    if(!pokemonChoisiAttribut==""){
                    stats.innerHTML = '';
                stats.classList.replace('attr', 'stats');
                pokemonChoisi = listePokemons.find((pokemon) => pokemon.name == pokemonChoisiAttribut);
            } else if (pokemonChoisiAttribut=="") {
                pokemonChoisi = listePokemons.find((pokemon) => pokemon.name == listeDeroulante.value);
            }
        console.log("pokemon choisi : " ,pokemonChoisiAttribut);

        

        stats.innerHTML = `<img id ="img" src="${pokemonChoisi.image}" alt=""/>`
        let img=document.getElementById('img');
  
let angle=0;
setInterval(function(){
    img.style.transform="rotateZ("+ angle++ +"deg)";
}, 30);
        
        let statistique = document.createElement("div");
        statistique.setAttribute("class" , "statistique");
        stats.appendChild(statistique);

        for (const [propriete, valeur] of Object.entries(pokemonChoisi.stats)) {
            let  uneStat = document.createElement("p");
            uneStat.textContent = `${propriete} : ${valeur}`;
            statistique.appendChild(uneStat);  
        }
        pokemonChoisiAttribut="";
}

    function attributFunction(pokemonAttribut) {
        for (let j = 0; j < pokemonAttribut.length; j++) {
            let nameParAttribut = pokemonAttribut[j].name;
            
            stats.classList.replace('stats', 'attr');

            let attributAffichage = document.createElement("div");
            attributAffichage.setAttribute("class", "attribut");
            stats.appendChild(attributAffichage);

            let affichageResultatAttribut = document.createElement("p");
            affichageResultatAttribut.textContent = nameParAttribut;
            attributAffichage.appendChild(affichageResultatAttribut);

        }
        const paragraphe=  document.querySelectorAll("p");
        for (let k = 0; k < paragraphe.length; k++) {
            paragraphe[k].addEventListener("click",function () {
            pokemonChoisiAttribut=paragraphe[k].textContent;
            // console.log("cliquer sur : " ,pokemonChoisi);
            pokemonFunction();
            
            })
       } 
    }

function verifListChecked(){
    
    for (let elem of document.querySelectorAll('input[type="radio"][name="listepokemon"]')) {
        elem.addEventListener("input", (event) => {  
            stats.innerHTML = "";
            if (listPokemonByAttr.checked){

               stats.innerHTML="";
                selectList.options.length = 0;
                for (let i = 0; i < listAttributPokemon.length; i++) {
                    attributPokemon= listAttributPokemon[i];
                    let option = document.createElement("option");
                  
                    option.value= attributPokemon.name;
                    option.id = attributPokemon.id;
                    option.innerHTML = attributPokemon.name;
                    listeDeroulante.appendChild(option);
                //    console.log(listeDeroulante);
                   const labelElement = document.getElementById('caract');
                   labelElement.textContent = "Voici la liste de pokemon :";
                }

            }else {
                garnirSelectList();

            } 
        });
    }
}

/**
 * Génère dynamiquement les options de l'élément <select>
 */
function garnirSelectList() {
    selectList.options.length = 0;
    // document.body.appendChild(listeDeroulante);
    for (let i = 0; i < listePokemons.length; i++) {
        
        unPokemon = listePokemons[i];
        let option = document.createElement("option");
        
        option.value= unPokemon.name;
        option.id = unPokemon.id;
        option.innerHTML = unPokemon.name;
        listeDeroulante.appendChild(option);   
    }
}

function getPokemonsList () {
    return new Promise((resolve) => {
        return resolve(
            fetch("https://pokebuildapi.fr/api/v1/pokemon/limit/10", {
                method: 'GET',
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'Content-type': 'application/json'
                }
                
            }).then(function(response) {
            
                return response.json();
            })
        );
    });
}

function getPokemonsAttribut () {

    return new Promise((resolve) => {
        return resolve(
            fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'Content-type': 'application/json'
                }
                
            }).then(function(response) {
            
                return response.json();
            })
        );
    });
}