var express = require('express');
var passport = require('passport');
var validator = require('validator');

var User = require('../models/user');
var models = require('../models');

var router = express.Router();

/* UNAUTHENTICATED ACCESS */
router.get('/sign-up', function(req, res) {
    res.render('sign-up', { flash: req.flash('signupMessage') });
});

router.get('/login', function(req, res) {
    res.render('login', { flash: req.flash('loginMessage') });
});

// process the sinup form
router.post('/sign-up', passport.authenticate('local-signup', {
    successRedirect : '/market', // redirect to the profile setup
    failureRedirect : '/sign-up', // redirect back to the signup page if there is an error
    failureFlash : true // allow flash messages
}));

// process the login form
router.post('/login', passport.authenticate('local-login', {
    successRedirect : '/market', // redirect to the index
    failureRedirect : '/login', // redirect back to the signup page if there is an error
    failureFlash : true // allow flash messages
}));

router.get('/forgotten-password', function(req, res) {
    res.redirect('/market');
});

router.get('/', function(req, res) {
	res.redirect('/market');
});

router.use('/market', require('./market'));

router.use(isLoggedIn);

router.use('/portfolio', require('./portfolio'));


router.get('/logout', function(req, res) {
    req.logout();
    res.redirect('/');
});

//router.use(isSetup);

/* AUTHENTICATED ACCESS */



/* HELPER FUNCTIONS */

function isLoggedIn(req, res, next) {
    if(req.isAuthenticated()) {
        return next();
    }

    res.redirect('/login');
}

function isSetup(req, res, next) {
    if(req.user) {
    	return next();
    }

    res.redirect('/welcome');
}

module.exports = router;

(1/2 * 3, aba, "asdf", [1,2,3]) => {
    return null;
}