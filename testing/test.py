import logging
import unittest
import time
import kb

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


    def test_modifications(self):

        # check no exception is raised
        self.kb.add(["johnny rdf:type Human", "johnny rdfs:label \"A que Johnny\""])
        self.kb += ["alfred rdf:type Human", "alfred likes icecream"]
        self.kb.retract(["alfred rdf:type Human", "alfred likes icecream"])
        self.kb -= ["johnny rdf:type Human"]

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

        self.assertTrue('alfred' in self.kb)
        self.assertFalse('tartempion' in self.kb)

        self.assertTrue('alfred likes icecream' in self.kb)
        self.assertTrue('alfred likes *' in self.kb)
        self.assertTrue('alfred likes ?smthg' in self.kb)
        self.assertFalse('alfred likes mygrandmother' in self.kb)

        self.kb -= ["alfred rdf:type Human", "alfred likes icecream"]

        self.assertItemsEqual(self.kb["* rdf:type Human"],
                              ['johnny'])

        self.assertFalse('alfred likes icecream' in self.kb)
        self.assertFalse('alfred' in self.kb)

    def _test_events(self):

        eventtriggered = False

        def onevent(evt):
            eventtriggered = True

        self.kb.subscribe(["?o isIn room"], onevent)

        self.kb += ["alfred isIn room"]

        time.sleep(1)

        self.assertTrue(eventtriggered)

        self.kb.methods()


if __name__ == '__main__':

    kblogger = logging.getLogger("kb")
    console = logging.StreamHandler()
    kblogger.setLevel(logging.DEBUG)
    kblogger.addHandler(console)
    
    unittest.main()
