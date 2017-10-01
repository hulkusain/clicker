const socket = io(window.location.origin);

var click = document.getElementById('click');
var scorebox = document.getElementById('score');
var upgradebox = document.getElementById('upgrade');
var clickbox = document.getElementById('clickers');
var achievements = document.getElementById('achievements');
var achieveclick = document.getElementById('achieve-click');
var achievelottery = document.getElementById('achieve-lottery');
var achievetotal = document.getElementById('achieve-total');
var frenzy = document.getElementById('frenzy')
var lotterystatus = document.getElementById('status');
var lottery = document.getElementById('lottery');
var lotterymodal = document.getElementById('lottery-modal');
var lotteryerror = document.getElementById('lottery-error');
var lotteryguess = document.getElementById('guess');
var lotteryopen = document.getElementById('lottery-open');
var lotteryupdate = true;
var score = 0;
var isfrenzy = false;
var clickValue;

var lottery_default = "Guess a number below "
var lottery_correct = "Correct, you've won "
var lottery_incorrect = "Incorrect"

var unlock_template = `
  <div class="container">
    <div class="row justify-content-center">
      <h5>{0} Unlock</h5>
    </div>
    <div class="row justify-content-center">
      <div class="col-sm-auto">
        Value: {1}
      </div>
      <div class="col-sm-auto">
        Price: {2}
      </div>
    </div>
  </div>
`;

var upgrade_template = `
  <div class="container">
    <div class="row justify-content-center">
      <h5>{0}</h5>
    </div>
    <div class="row justify-content-center">
      <div class="col-sm-auto">
        {1}: {2}
      </div>
      <div class="col-sm-auto">
        Price: {3}
      </div>
    </div>
  </div>
`;

var click_template = `
  <div class="container">
    <div class="row justify-content-center">
      <h5>{0}</h5>
    </div>
    <div class="row justify-content-center">
      <div class="col-sm-auto">
        Click: {1}
      </div>
      <div class="col-sm-auto">
        Multiplier: {2}
      </div>
      <div class="col-sm-auto">
        Total: {3}
      </div>
    </div>
  </div>
`;

String.prototype.format = function() {
  a = this;
  for (k in arguments) {
    a = a.replace("{" + k + "}", arguments[k])
  }
  return a
}

function createTemplate(template) {
  var list_item = document.createElement('li');
  list_item.className += "list-group-item";
  list_item.innerHTML = template;
  return list_item;
}

function createUpgradeTemplate(name, upgrades) {
  var position = name.indexOf('Click');
  fmt_name = [name.slice(0, position), ' ', name.slice(position)].join('');
  if ('value' in upgrades) {
    var amount = upgrades['value'];
    var price = upgrades['v-price'];
    var type = 'Click';
    var template = upgrade_template.format(fmt_name, type, amount, price);
    var upgrade = createTemplate(template);
    upgrade.addEventListener('click', function(e){
      e.preventDefault();
      socket.emit('upgrade', {'name': name, 'type': 'value'});
    });
    upgradebox.appendChild(upgrade);
  }

  if ('mult' in upgrades) {
    var amount = upgrades['mult'];
    var price = upgrades['m-price'];
    var type = 'Multiplier';
    var template = upgrade_template.format(fmt_name, type, amount, price);
    var upgrade = createTemplate(template);
    upgrade.addEventListener('click', function(e){
      e.preventDefault();
      socket.emit('upgrade', {'name': name, 'type': 'mult'});
    });
    upgradebox.appendChild(upgrade);
  }
}

function createUnlockableTemplate(name, unlockable) {
  var position = name.indexOf('Click')
  fmt_name = [name.slice(0, position), ' ', name.slice(position)].join('');
  var value = unlockable['value'];
  var price = unlockable['price'];
  var template = unlock_template.format(fmt_name, value, price);
  var unlock = createTemplate(template)
  unlock.addEventListener('click', function(e){
    e.preventDefault();
    socket.emit('upgrade', {'name': name, 'type': 'value'});
  });
  upgradebox.appendChild(unlock);
}

function createClickerTemplate(name, clicker) {
  var position = name.indexOf('Click')
  fmt_name = [name.slice(0, position), ' ', name.slice(position)].join('');
  var value = clicker['value'];
  var mult = clicker['mult'];
  var total = value * mult;
  if (name === 'BaseClick' && isfrenzy){
    total *= 2
  }
  var template = click_template.format(fmt_name, value, mult, total);
  clickbox.appendChild(createTemplate(template));
}

function update() {
  socket.emit('update', function(data) {
    if (!data) {
      scorebox.innerHTML = "Connection Invalid";
      return
    }
    isfrenzy = data['frenzy']
    if (!data['frenzy_avail']) {
      frenzy.classList.add('disable');
    } else {
      frenzy.classList.remove('disable');
    }
    score = data['score']
    scorebox.innerHTML = score;
    if (lotteryupdate) {
      lotterystatus.innerHTML = lottery_default + data['limit'];
      lotteryupdate = false;
    }
    var clickers = data['clickers'];
    while (upgradebox.hasChildNodes()) {
      upgradebox.removeChild(upgradebox.lastChild);
    }
    while (clickbox.hasChildNodes()) {
      clickbox.removeChild(clickbox.lastChild);
    }
    for (var name in data['upgrades']) {
      createUpgradeTemplate(name, data['upgrades'][name]);
    }
    for (var name in data['unlockables']) {
      createUnlockableTemplate(name, data['unlockables'][name]);
    }
    for (var name in data['clickers']) {
      createClickerTemplate(name, data['clickers'][name])
      if (name === 'BaseClick') {
        clickValue = data['clickers'][name]['value'] * data['clickers'][name]['mult']
      }
    }
  });
}

click.addEventListener('click', function(e) {
  e.preventDefault();
  score += clickValue;
  if (isfrenzy) {
    score += clickValue;
  }
  scorebox.innerHTML = score;
  socket.emit('click', 'BaseClick');
});

lottery.addEventListener('click', function(e) {
  e.preventDefault();
  guess = lotteryguess.value;
  if (guess === "") {
    lotteryerror.innerHTML = "Please input a number";
  } else {
    socket.emit('lottery', guess, function(data) {

      if (data == null) {
        lotteryerror.innerHTML = "Invalid Input";
      } else {
        lotteryguess.style.display = 'none';
        lotteryerror.style.display = 'none';
        lottery.style.display = 'none';
        lotteryupdate = false;
        if (data == 0) {
          lotterystatus.innerHTML = lottery_incorrect;
        } else {
          lotterystatus.innerHTML = lottery_correct + data;
        }
      }
    });
  }
});

lotteryopen.addEventListener('click', function(e) {
  lotteryguess.style.display = 'block';
  lotteryerror.style.display = 'block';
  lottery.style.display = 'block';
  lotteryupdate = true;
  lotteryerror.innerHTML = "";
  lotteryguess.value = "";
});

achievements.addEventListener('click', function(e) {
  socket.emit('achievements', function(data){
    if (!data) {
      return
    }
    achieveclick.innerHTML = data['click']
    achievelottery.innerHTML = data['lottery']
    achievetotal.innerHTML = data['total']
  });
});

frenzy.addEventListener('click', function(e) {
  socket.emit('frenzy');
});

var updateLoop = setInterval(update, 1000);


function test() {
  var xhr = new XMLHttpRequest();
  xhr.open('POST', '/login', true);
  xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
  xhr.onload = function () {
      // do something to response
      console.log(this.responseText);
  };
  xhr.send('username=test1&password=password');
}
