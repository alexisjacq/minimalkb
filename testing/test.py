#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import unittest
import time
import kb
from minimalkb import __version__

from Queue import Empty

REASONING_DELAY = 0.2

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.kb = kb.KB()
        self.kb.clear()

    def tearDown(self):
        self.kb.close()

    def test_basics(self):

        self.kb.hello()

        with self.assertRaises(kb.KbError):
            self.kb.add()
        with self.assertRaises(kb.KbError):
            self.kb.add("toto")

    def test_basic_modifications(self):

        # check no exception is raised
        self.kb.add(["johnny rdf:type Human", "johnny rdfs:label \"A que Johnny\""])
        self.kb += ["alfred rdf:type Human", "alfred likes icecream"]
        self.kb.retract(["alfred rdf:type Human", "alfred likes icecream"])
        self.kb -= ["johnny rdf:type Human"]

    def test_modifications(self):

        self.assertFalse(self.kb["* * *"])
        
        self.kb += ["alfred rdf:type Human"]
        self.assertItemsEqual(self.kb["* * *"], 
                              [['alfred', 'rdf:type', 'Human']])

        self.kb -= ["alfred rdf:type Human"]
        self.assertFalse(self.kb["* * *"])

        self.kb += ["alfred rdf:type Human", "alfred likes icecream"]
        self.assertItemsEqual(self.kb["* * *"], 
                              [['alfred', 'likes', 'icecream'],
                               ['alfred', 'rdf:type', 'Human']])


    def test_existence(self):

        self.assertFalse('alfred' in self.kb)
        self.assertFalse('alfred likes icecream' in self.kb)
        self.assertFalse('alfred likes *' in self.kb)

        self.kb += ["alfred rdf:type Human", "alfred likes icecream"]

        self.assertTrue('alfred' in self.kb)
        self.assertFalse('tartempion' in self.kb)

        self.assertFalse('alfred likes' in self.kb)
        self.assertTrue('alfred likes icecream' in self.kb)
        self.assertTrue('alfred likes *' in self.kb)
        self.assertTrue('alfred likes ?smthg' in self.kb)
        self.assertTrue('* likes *' in self.kb)
        self.assertFalse('* dislikes *' in self.kb)
        self.assertTrue('?toto likes *' in self.kb)
        self.assertFalse('alfred likes mygrandmother' in self.kb)

        self.kb -= ["alfred rdf:type Human", "alfred likes icecream"]

        self.assertFalse('alfred likes icecream' in self.kb)
        self.assertFalse('alfred' in self.kb)

    def test_existence_with_inference(self):
        """ Requires a RDFS reasoner to run.
        """
        self.kb += ["alfred rdf:type Human", "Human rdfs:subClassOf Animal"]
        time.sleep(REASONING_DELAY)
        self.assertTrue('alfred rdf:type Animal' in self.kb)

        self.kb += ["Animal rdfs:subClassOf Thing"]
        time.sleep(REASONING_DELAY)
        self.assertTrue('alfred rdf:type Thing' in self.kb)

    def _test_lookup(self):
        self.assertItemsEqual(self.kb.lookup('alfred'), [])

        self.kb += ["alfred rdf:type Robot"]
        self.assertItemsEqual(self.kb.lookup('alfred'), [('alfred', 'instance')])

        self.kb += ["nono rdfs:label \"alfred\""]
        self.assertItemsEqual(self.kb.lookup('alfred'), [('alfred', 'instance'), ('nono', 'unknown')])

        self.assertItemsEqual(self.kb.lookup('Robot'), [('Robot', 'class')])

    def test_retrieval(self):

        self.assertFalse(self.kb.about("Human"))
        self.assertFalse(self.kb["* rdf:type Human"])

        self.kb += ["johnny rdf:type Human", "johnny rdfs:label \"A que Johnny\""]
        self.kb += ["alfred rdf:type Human", "alfred likes icecream"]

        self.assertItemsEqual(self.kb.about("Human"), 
                            [['johnny', 'rdf:type', 'Human'],
                             ['alfred', 'rdf:type', 'Human']])

        self.assertItemsEqual(self.kb["* rdf:type Human"],
                              ['johnny', 'alfred'])

        self.kb -= ["alfred rdf:type Human", "alfred likes icecream"]

        self.assertItemsEqual(self.kb["* rdf:type Human"],
                              ['johnny'])


    def _test_complex_queries(self):
        self.assertItemsEqual(self.kb["?agent rdf:type Robot", "?agent desires ?obj"], [])

        self.kb += ["nono rdf:type Human", "alfred rdf:type Robot"]
        self.assertItemsEqual(self.kb["* * *"], [["nono", "rdf:type", "Human"], ["alfred", "rdf:type", "Robot"]])

        self.kb += ["nono desires jump", "alfred desires oil"]
        self.assertItemsEqual(self.kb["* * *"], [["nono", "desires", "jump"], ["alfred", "desires", "oil"], ["nono", "rdf:type", "Human"], ["alfred", "rdf:type", "Robot"]])
        self.kb += ["jump rdf:type Action"]

        self.assertItemsEqual(self.kb["?agent rdf:type Robot", "?agent desires ?obj"], [{"agent":"alfred", "obj":"oil"}])
        self.assertItemsEqual(self.kb["?agent desires ?act", "?act rdf:type Action"], [{"agent":"nono", "act":"jump"}])
        self.assertItemsEqual(self.kb["?agent desires ?obj"], [{"agent":"alfred", "obj":"oil"}, {"agent":"nono", "obj":"jump"}])

    def _test_update(self):
        self.kb += ["nono isNice true", "isNice rdf:type owl:FunctionalProperty"]
        self.assertItemsEqual(self.kb["* isNice true"], ['nono'])

        self.kb += ["nono isNice false"]
        self.assertFalse(self.kb["* isNice true"])
        self.assertItemsEqual(self.kb["* isNice false"], ['nono'])


    def test_events(self):

        eventtriggered = [False]

        def onevent(evt):
            #py3 only! -> workaround is turning eventtriggered into a list
            #nonlocal eventtriggered
            print("In callback. Got evt %s" % evt)
            eventtriggered[0] = True

        self.kb.subscribe(["?o isIn room"], onevent)

        # should not trigger an event
        self.kb += ["alfred isIn garage"]
        time.sleep(0.1)
        self.assertFalse(eventtriggered[0])


        # should trigger an event
        self.kb += ["alfred isIn room"]
        time.sleep(0.1)
        self.assertTrue(eventtriggered[0])

        eventtriggered[0] = False

        # should not trigger an event
        self.kb += ["alfred leaves room"]
        time.sleep(0.1)
        self.assertFalse(eventtriggered[0])

        # alfred is already in garage, should not fire an event
        self.kb.subscribe(["?o isIn garage"], onevent)
        time.sleep(0.1)
        self.assertFalse(eventtriggered[0])

        # alfred is already in garage, should not fire an event
        self.kb += ["alfred isIn garage"]
        time.sleep(0.1)
        self.assertFalse(eventtriggered[0])

        self.kb += ["batman isIn garage"]
        time.sleep(0.1)
        self.assertTrue(eventtriggered[0])

    def test_polled_events(self):

        evtid = self.kb.subscribe(["?o isIn room"])

        # should not trigger an event
        self.kb += ["alfred isIn garage"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()

        # should trigger an event
        self.kb += ["alfred isIn room"]
        time.sleep(0.1)

        id, value = self.kb.events.get_nowait()
        self.assertEqual(id, evtid)
        self.assertItemsEqual(value, [u"alfred"])

        # should not trigger an event
        self.kb += ["alfred leaves room"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()


        # alfred is already in garage, should not fire an event
        evtid = self.kb.subscribe(["?o isIn garage"])
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()

        # alfred is already in garage, should not fire an event
        self.kb += ["alfred isIn garage"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()


        self.kb += ["batman isIn garage"]
        time.sleep(0.1)

        id, value = self.kb.events.get_nowait()
        self.assertEqual(id, evtid)
        self.assertItemsEqual(value, [u"batman"])

    def test_complex_events(self):

        evtid = self.kb.subscribe(["?a desires ?act", "?act rdf:type Action"], var="a")

        # should not trigger an event
        self.kb += ["alfred desires ragnagna"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()

        # should not trigger an event
        self.kb += ["ragnagna rdf:type Zorro"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()


        # should trigger an event
        self.kb += ["ragnagna rdf:type Action"]
        time.sleep(0.1)

        id, value = self.kb.events.get_nowait()
        self.assertEqual(id, evtid)
        self.assertItemsEqual(value, [u"alfred"])

    def test_complex_events_rdfs(self):
        """ Requires a RDFS reasoner to run.
        """
        evtid = self.kb.subscribe(["?a desires ?act", "?act rdf:type Action"], var = "a")

        # should not trigger an event
        self.kb += ["alfred desires ragnagna"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()

        # should not trigger an event
        self.kb += ["ragnagna rdf:type Zorro"]
        time.sleep(0.1)

        with self.assertRaises(Empty):
            self.kb.events.get_nowait()

        # should trigger an event
        self.kb += ["Zorro rdfs:subClassOf Action"]
        time.sleep(REASONING_DELAY)
        # required to ensure the event is triggered after classification!
        self.kb += ["nop nop nop"]
        time.sleep(0.1)

        id, value = self.kb.events.get_nowait()
        self.assertEqual(id, evtid)
        self.assertItemsEqual(value, [u"alfred"])

    def test_taxonomy_walking(self):

        self.assertFalse(self.kb.classesof("john"))
        self.kb += ["john rdf:type Human"]
        self.assertItemsEqual(self.kb.classesof("john"), [u'Human'])
        self.kb += ["john rdf:type Genius"]
        self.assertItemsEqual(self.kb.classesof("john"), [u'Human', u'Genius'])
        self.kb -= ["john rdf:type Human"]
        self.assertItemsEqual(self.kb.classesof("john"), [u'Genius'])

    def test_taxonomy_walking_inheritance(self):
        """ Requires a RDFS reasoner to run.
        """
        self.kb += ["john rdf:type Human"]
        self.assertItemsEqual(self.kb.classesof("john"), [u'Human'])
        self.kb += ["Human rdfs:subClassOf Animal"]
        time.sleep(REASONING_DELAY)
        self.assertItemsEqual(self.kb.classesof("john"), [u'Human', u'Animal'])
        self.assertItemsEqual(self.kb.classesof("john", True), [u'Human'])
        self.kb -= ["john rdf:type Human"]
        time.sleep(REASONING_DELAY)
        self.assertFalse(self.kb.classesof("john"))

def version():
    print("minimalKB tests %s" % __version__)

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Test suite for minimalKB.')
    parser.add_argument('-v', '--version', action='version',
                       version=version(), help='returns minimalKB version')
    parser.add_argument('-f', '--failfast', action='store_true',
                                help='stops at first failed test')

    args = parser.parse_args()


    kblogger = logging.getLogger("kb")
    console = logging.StreamHandler()
    kblogger.setLevel(logging.DEBUG)
    kblogger.addHandler(console)
    
    unittest.main(failfast=args.failfast)
