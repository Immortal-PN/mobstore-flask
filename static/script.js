window.addEventListener("scroll", reveal);

function reveal(){

let reveals = document.querySelectorAll(".reveal");

for(let i = 0; i < reveals.length; i++){

let windowHeight = window.innerHeight;
let elementTop = reveals[i].getBoundingClientRect().top;
let elementVisible = 120;

if(elementTop < windowHeight - elementVisible){

reveals[i].classList.add("active");

}

}
}