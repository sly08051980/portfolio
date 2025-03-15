console.log("script chargé");

const motAleatoire="bricolage";
const nbrCoup=8;
let alphabet=["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"];
let boutton;
let bouttonCliquer;
let btn ="";

let lettreChercher=[];
let lettreTrouvee = false;
let lettreIdentique=false;
let essaie=7;
let tiret;
const imagePendu=['./assets/images/un.png','./assets/images/deux.png','./assets/images/trois.png','./assets/images/quatre.png','./assets/images/cinq.png','./assets/images/six.png','./assets/images/sept.png','./assets/images/six.png'];
let indeximage=0;


let header = document.createElement("header");
document.body.appendChild(header);

let titre = document.createElement("h1");
titre.innerText="PENDU";
header.appendChild(titre);


let main = document.createElement("main");
document.body.appendChild(main);

let divSpan= document.createElement("div");
divSpan.setAttribute("class","divSpan");
main.appendChild(divSpan);

let nbrEssaieText = document.createElement("span");
nbrEssaieText.innerText="Nbr de coup restant : "
divSpan.appendChild(nbrEssaieText);

let essaieAffiche= document.createElement("span");
essaieAffiche.innerText=essaie;
divSpan.appendChild(essaieAffiche);

let divTiret = document.createElement("div")
divTiret.setAttribute("class","TiretMot");
main.appendChild(divTiret);

for (let i = 0; i < motAleatoire.length; i++) {
    


    tiret = document.createElement("p");
    tiret.setAttribute("id","lettre_"+motAleatoire[i])
    tiret.innerText="_";
    divTiret.appendChild(tiret);
    
}

let div = document.createElement("div")
div.setAttribute("class","image");
main.appendChild(div);
let imgPendu = document.createElement("img");

   imgPendu.src=imagePendu[indeximage];

div.appendChild(imgPendu);

let boutonClass = document.createElement("div");
boutonClass.setAttribute("class", "boutonClass");
main.appendChild(boutonClass);



for (let i = 0; i < alphabet.length; i++) {
    let boutonAlphabet = alphabet[i];
    boutton = document.createElement("button");
    boutton.setAttribute("id", boutonAlphabet);
    boutton.innerText = boutonAlphabet;
    boutonClass.appendChild(boutton);
    boutton.addEventListener("click", choisirLettre);
}

function choisirLettre() {
    bouttonCliquer = this; 
    console.log("this : ", this);
    btn = bouttonCliquer.id;
    console.log("btn : ", btn);

    rechercherLettreRechercher(btn,lettreChercher);
    

}


function rechercheLettre(btn,lettreTrouvee) {



         for (let ind = 0; ind < motAleatoire.length; ind++) {
        if (btn === motAleatoire[ind]) {
            lettreTrouvee = true;
            break;
        }
     }

     if (lettreTrouvee) {
        document.getElementById(btn).style.backgroundColor="blue";
      let tot=  document.getElementById("lettre_"+btn);
         tot.innerText=btn;
         
        console.log("ok");
     } else {
        document.getElementById(btn).style.backgroundColor="red";
         console.log("non");
        essaie=essaie-1;
         essaieAffiche.innerText=essaie;
         image();

        


         if(essaie==0){
            console.log("perdu");
            let divRejour = document.createElement("div");
            divRejour.setAttribute("class","btnRejouer");
            main.appendChild(divRejour);

            let buttonRejouer= document.createElement("button")
            buttonRejouer.innerText="Rejouer";
            divRejour.appendChild(buttonRejouer);
            buttonRejouer.addEventListener("click",rejouer);
            imgPendu.src="./assets/images/perdu.png";

            div.appendChild(imgPendu);

            boutonClass.style.display="none";


         }
         console.log(essaie);
     }
    
}



function rechercherLettreRechercher(btn, lettreChercher) {
         if (lettreChercher.find((lettre) => lettre == btn) === btn) {
            console.log("lettre déjà tapée");
         } else {
            console.log("lettre non tapée");
            lettreChercher.push(btn);
            rechercheLettre(btn,lettreTrouvee);
            let resultat = verifGagner();
            console.log((resultat));
         }
}

function rejouer(){
    location.reload(),false;
}


function image(){

    indeximage=indeximage+1;
    imgPendu.src=imagePendu[indeximage];

    div.appendChild(imgPendu);
}


function verifGagner(){
    let tirets = document.querySelectorAll(".TiretMot > p");

 let gagne = true;
    
    tirets.forEach(unTiret => {
        console.log("Un tiret : ", unTiret);
        
       
       
        if(unTiret.innerText === "_" ) {
            gagne = false;
           
        
        }
               
        
    
    })
    if(gagne===true){
        imgPendu.src="./assets/images/gagner.jpg";
        div.appendChild(imgPendu);
        let divRejour = document.createElement("div");
        divRejour.setAttribute("class","btnRejouer");
        main.appendChild(divRejour);

        let buttonRejouer= document.createElement("button")
        buttonRejouer.innerText="Rejouer";
        divRejour.appendChild(buttonRejouer);
        buttonRejouer.addEventListener("click",rejouer);
      

        div.appendChild(imgPendu);
    
        boutonClass.style.display="none";
    }
    return gagne;

}
