function openForm(n) {
  document.getElementById("popupForm").style.display = "block";
  currentIndex = n;
  //alert(n);
}
function closeForm() {
  document.getElementById("popupForm").style.display = "none";
}

function buildInner(total, value, index, array){
  row='<tr><td>'+
      '<button class="feeButton" onclick="setFee('+value["median"]+','+index+')" id="mfee'+index+'"><strong>'+value["median"]+'</strong></button></td><td>'+
      '<button class="feeButton" onclick="setFee('+value["avg"]+','+index+')" id="afee'+index+'"><strong>'+value["avg"]+'</strong></button></td><td>'+
      '<button class="feeButton" onclick="setFee('+value["cappedAvg"]+','+index+')" id="cfee'+index+'"><strong>'+value["cappedAvg"]+'</strong></button></td>'+
      '<td><div class="alias" id="alias'+index+'">'+value["alias"]+'</div></td>'+
      '<td><button class="feeButton" id="isfee'+index+'" onclick="setFee('+value["curFee"]+','+index+')"><strong>'+value["curFee"]+'</strong></button></td>'+
      '<td><input type="text" class="newfee" id="newfee'+index+'" value="'+Math.round((value["curFee"]+value["median"]+value["cappedAvg"])/3)+'"></td>'+
      '<td><button onclick="openForm('+index+')"><strong>Copy</strong></button></td></tr>';
  //console.log(row);
  return(total+row);
}

function setFee(fee,i){
  document.getElementById('newfee'+i).value=Math.round(fee);
}

function buildContent(inner,alias,pubkey){
console.log(pubkey);
start='<h2>Fee suggestions for Node:'+alias+'</h2>'+
      '<p>Click on the copy button to open the copy menu.</p><a href="https://flask.einseins11.de/'+
      'lnpixi?addNode='+pubkey+'">Update Data</a>'+
      '<table class="itemRow">'+
      '<tr><th>Med</th><th>Avg</th><th>cAvg</th><th>Peers Alias</th><th>Current Fee</th><th>New Fee</th><th></th></tr>';
//alert(typeof(inner));
//console.log(inner);
end='<div class="copyMenu" id="copyMenu">'+
      '<div class="formPopup" id="popupForm">'+
        '<form action="None" class="formContainer">'+
          '<strong>Copy</strong>'+
          '<button type="button" class="btn" onclick="cplncli(1)">ln-cli</button>'+
          '<button type="button" class="btn" onclick="cpcl(1)">c-lightning</button>'+
          '<button type="button" class="btn" onclick="cpfee(1)">fee</button>'+
          '<button type="button" class="btn" onclick="cpcid(1)">chan-id</button>'+
          '<button type="button" class="btn" onclick="cpcpoint(1)">chan-point</button>'+
          '<button type="button" class="btn" onclick="cpnode(1)">node-pubkey</button>'+
          '<button type="button" class="btn cancel" onclick="closeForm()">Close</button>'+
        '</form></div></div>';

return(start+inner+end);
}

function cplncli(n) {
  if (n>0){
    cptext="./lncli --fee_rate " + document.getElementById("newfee"+currentIndex).value + " " + suggestionCluster[currentIndex]["chanPoint"];
  }
  else{
    cptext="baue shellscript fuer alle. not yet ready"
  }
  navigator.clipboard.writeText(cptext);
  return;
}

function cpcl(n) {
  if (n>0){
    cptext="#not yet done ./lightning-cli lightning-setchannelfee" + document.getElementById("newfee"+currentIndex).value + " " + suggestionCluster[currentIndex]["chanPoint"];
  }
  else{
    cptext="baue shellscript fuer alle. not yet ready"
  }
  navigator.clipboard.writeText(cptext);
  return;
}

function cpfee(n){
  navigator.clipboard.writeText(document.getElementById("newfee"+currentIndex).value);
  return;
}

function cpcid(n){
  navigator.clipboard.writeText(suggestionCluster[currentIndex]["chanID"]);
  return;
}

function cpcpoint(n){
  navigator.clipboard.writeText(suggestionCluster[currentIndex]["chanPoint"]);
  return;
}

function cpnode(n){
  navigator.clipboard.writeText(suggestionCluster[currentIndex]["pubkey"]);
  return;
}
