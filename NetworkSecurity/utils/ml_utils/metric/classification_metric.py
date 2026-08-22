import os 
import sys
import numpy as np 
import pandas as pd 

from NetworkSecurity.entity.artifacts_entity import ClassificationMetricArtifact
from NetworkSecurity.exception.exception import NetworkSecurityException

from sklearn.metrics import f1_score,precision_score,recall_score

def get_classification_score(y_true,y_pred)->ClassificationMetricArtifact:
    try:
        model_f1_score = float(f1_score(y_true, y_pred))
        model_recall_score = float(recall_score(y_true, y_pred))
        model_precision_score = float(precision_score(y_true, y_pred))
        
        classification_metric=ClassificationMetricArtifact(
            f1_score=model_f1_score,
            precision_score=model_precision_score,
            recall_score=model_recall_score)
        
        return classification_metric
    except Exception as e:
        raise NetworkSecurityException(e,sys)