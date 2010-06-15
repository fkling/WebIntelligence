'''
Created on Jun 6, 2010

'''

import numpy as np
import itertools, math


class TDMBuilder(object):
    """ Provides basic functionality for build TDMs.
    
        
        INPUT:
            - terms: The terms that are used in the matrix
            - documents: Document IDs
        
        Currently supported weighting schemes:
         
        Local:
            - Binary (0)
            - Term frequency (1)
            - Logarithmic (2)
            - Augmented normal (3)
            
        Global:
            - Binary (0)
            - Normal (1)
            - GFLDF (2)
            - LDF (3)
            - Entropy (4)
    
    """
    
    LOCAL_BINARY = 0
    LOCAL_TERM_FREQUENCY = 1
    LOCAL_LOG = 2
    LOCAL_AUGNORM = 3
    
    GLOBAL_BINARY = 0
    GLOBAL_NORMAL = 1
    GLOBAL_GFLDF = 2
    GLOBAL_LDF = 3
    GLOBAL_ENTROPY = 4
    
    
    def __init__(self, terms, documents):       
        self.terms = list(terms)
        self.documents = list(documents)
        
        #create some kind of ordered sets for fast access
        self.terms_set = dict(itertools.izip(self.terms, itertools.count()))
        self.documents_set = dict(itertools.izip(self.documents, itertools.count()))
        
        self.terms_len = len(self.terms)
        self.documents_len = len(self.documents)
        
        self.TF = np.matrix(np.zeros((self.terms_len, self.documents_len), dtype=np.float64))
        
        # method lookup table
        self.localm = [self.local_binary, self.local_term_frequency, 
                        self.local_log, self.local_augnorm]
        
        self.globalm = [self.global_binary, self.global_normal, 
                         self.global_gfldf, self.global_ldf, self.global_entropy]       
    
    def getTF(self):
        """ Returns the current term frequency matrix."""
        return self.TF
    
    def add_document_term(self, document, term):
        """ Add a term to the document vector. """
        
        if term in self.terms_set: 
            self.TF[self.terms_set[term],self.documents_set[document]] += 1
        
    def add_document_terms(self, document, terms):
        """ Add multiple terms to the document vector."""
        
        d = self.documents_set[document]
        for term in terms:
            if term in self.terms_set: 
                self.TF[self.terms_set[term],d] += 1
                
    def build_matrix(self, matrix=None, localw=None, globalw=None):
        """ Build the matrix using the specified local and global weighting 
            functions (default: binary).
        """

        localw = localw if localw is not None else TDMBuilder.LOCAL_BINARY
        globalw = globalw if globalw is not None else TDMBuilder.GLOBAL_BINARY
        
        A = matrix if matrix is not None else self.TF
        
        # increases performance for simple binary term document matrix
        # (no need to traverse the matrix)
        if localw == TDMBuilder.LOCAL_BINARY and globalw == TDMBuilder.GLOBAL_BINARY:
            return A.astype(np.bool)
        
        if localw == TDMBuilder.LOCAL_TERM_FREQUENCY and globalw == TDMBuilder.GLOBAL_BINARY:
            return A
        
        # store local references to functions for fast access
        localm = self.localm[localw]
        globalm = self.globalm[globalw]
        
        M = np.matrix(np.zeros((self.terms_len, self.documents_len)))
        for i in xrange(self.terms_len):
            for j in xrange(self.documents_len):
                M[i,j] =  localm(i,j, self.TF[i,j], A)
            M[i] *= globalm(i, A)
        return M
    
    def local_binary(self, i, j, t, matrix):
        return 0 if not t else 1
    
    def local_term_frequency(self, i, j, t, matrix):
        return t
    
    def local_log(self, i, j, t, matrix):
        return math.log(t + 1)
    
    def local_augnorm(self, i, j, t, matrix, d={}): # use d to simulate a static variable
        m = d.setdefault(j, matrix[:,j].max())
        return ((t/m) + 1) / 2
    
    def global_binary(self, i, j):
        return 1
    
    def global_normal(self, i, matrix):
        sum = 1.
        for j in xrange(self.documents_len):
            sum += matrix[i,j]**2
        return math.sqrt(1/sum)
    
    def global_gfldf(self, i, matrix):
        r = matrix[i]
        return float(r.sum())/1+r.astype(np.bool).sum()
    
    def global_ldf(self, i, matrix):
        return math.log(float(self.documents_len)/1+matrix[i].astype(np.bool).sum(), 2)
    
    def global_entropy(self, i, matrix):
        gf = float(matrix[i].astype(np.bool).sum())
        sum = 0.
        logn = math.log(self.documents_len)
        for j in xrange(self.documents_len):
            t = matrix[i,j]
            if t > 0:
                p = t / gf
                sum += (p * math.log(p)) / logn
        return 1 - sum
    

def compute_pca(M, dim=2):
    """ This method computes the PCA. 
    
        INPUT:
            - M: Term Document Matrix
            - dim: dimensions of the resulting matrix (default: 2)
            
        OUPUT:
            - matrix
    """
    
    m = np.mean(M, axis=1)            # 1. compute the mean          
    Xs = M - m                        # 2. subtract the mean
    S = np.cov(M)                     # 3. compute the covariance matrix
    w,V = np.linalg.eig(S)            # 4. compute the eigenvalues,-vectors

    # go through some conversions to sort the vectors by the eigenvalues
    # QUESTION: matrix.sort does not seem to support custom sort functions     
    Va = V.transpose().tolist()                # generate a list of columns  
    Va = map(tuple, Va)                        # need tuples to use them as dict keys
    dVa = dict(itertools.izip(Va, w))          #associate eigenvectors and eigenvalues
                 
    V = sorted(Va, key=dVa.get, reverse=True)      # 5. sort by eigenvalues
           
    V2 = np.matrix(V[0:dim]).astype(np.float64)    # eigenvectors contain complex values -> transform to reals
    U = V2*Xs                                      # 6. compute u_is  
    return U
    